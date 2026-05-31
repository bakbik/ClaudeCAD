#include <Wire.h>
#include "pid.h"
#include "motor_control.h"
#include "bluetooth_cmd.h"

// ── Pin map ──────────────────────────────────────────────────────────────────
// MPU-6050: SDA → A4, SCL → A5  (hardware I2C)
// L298N:  ENA → 9,  IN1 → 7,  IN2 → 6
//         ENB → 3,  IN3 → 5,  IN4 → 4
// HC-05:  RX  → 10, TX  → 11  (SoftwareSerial)

DualMotor motors(
  {9, 7, 6},   // left:  EN, IN1, IN2
  {3, 5, 4}    // right: EN, IN3, IN4
);
BluetoothCmd bt(10, 11);  // RX, TX

// ── PID ──────────────────────────────────────────────────────────────────────
// Starting gains — tune Kp first until it oscillates, then add Kd to damp,
// add Ki last (small) to remove steady-state lean.
PID balancePID(30.0f, 0.5f, 1.5f);

// ── MPU-6050 registers ───────────────────────────────────────────────────────
constexpr uint8_t MPU_ADDR   = 0x68;
constexpr uint8_t REG_PWR    = 0x6B;
constexpr uint8_t REG_ACCEL  = 0x3B;
constexpr uint8_t REG_GYRO_Z = 0x47;  // we only need gyro X for 2-wheel balance

// ── State ────────────────────────────────────────────────────────────────────
float   angle       = 0.0f;   // degrees from vertical (complementary filter)
float   setpoint    = 0.0f;   // target tilt; remote can bias this for fwd/bwd
int     steer       = 0;      // left/right differential
int     maxSpeed    = 200;    // PWM ceiling (0-255)
bool    fallen      = false;  // robot has tipped; motors cut until re-uprighted
unsigned long lastMs = 0;

// ── Complementary filter coefficient ─────────────────────────────────────────
constexpr float ALPHA = 0.98f;

void mpuInit() {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(REG_PWR);
  Wire.write(0x00);  // wake up
  Wire.endTransmission();
}

// Read all 14 bytes (accel XYZ, temp, gyro XYZ) in one I2C burst.
// Tilt axis: robot tips forward/backward around the wheel axle (X axis).
//   angle  = atan2(ay, az)  — tilt in the Y-Z plane
//   rate   = gx             — gyro X = rotation around wheel axle
void readMPU(float& ay, float& az, float& gx) {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(REG_ACCEL);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_ADDR, (uint8_t)14);

  Wire.read(); Wire.read();  // ax (unused)
  int16_t rawAy = (Wire.read() << 8) | Wire.read();
  int16_t rawAz = (Wire.read() << 8) | Wire.read();
  Wire.read(); Wire.read();  // temperature
  int16_t rawGx = (Wire.read() << 8) | Wire.read();
  // remaining gyro Y/Z bytes will drain on next read automatically

  ay = rawAy / 16384.0f;  // ±2g range
  az = rawAz / 16384.0f;
  gx = rawGx / 131.0f;    // ±250°/s range → deg/s
}

void setup() {
  Serial.begin(115200);
  Wire.begin();
  mpuInit();
  motors.begin();
  bt.begin(9600);
  lastMs = millis();
  Serial.println(F("BalanceBot ready"));
}

void loop() {
  unsigned long now = millis();
  float dt = (now - lastMs) / 1000.0f;
  if (dt < 0.005f) return;  // ~100 Hz cap
  lastMs = now;

  // ── Read sensor ───────────────────────────────────────────────────────────
  float ay, az, gx;
  readMPU(ay, az, gx);

  float accelAngle = atan2(ay, az) * 57.2958f;  // radians → degrees
  angle = ALPHA * (angle + gx * dt) + (1.0f - ALPHA) * accelAngle;

  // ── Fall detection (> 45° means it tipped) ───────────────────────────────
  if (abs(angle) > 45.0f) {
    if (!fallen) { fallen = true; motors.stop(); balancePID.reset(); }
    return;
  }
  fallen = false;

  // ── Bluetooth commands ────────────────────────────────────────────────────
  switch (bt.read()) {
    case Cmd::FORWARD:    setpoint = -3.0f; steer = 0;    break;
    case Cmd::BACKWARD:   setpoint =  3.0f; steer = 0;    break;
    case Cmd::LEFT:       steer = -60;                     break;
    case Cmd::RIGHT:      steer =  60;                     break;
    case Cmd::STOP:       setpoint = 0.0f;  steer = 0;    break;
    case Cmd::SPEED_UP:   maxSpeed = min(255, maxSpeed+10); break;
    case Cmd::SPEED_DOWN: maxSpeed = max(50,  maxSpeed-10); break;
    default: break;
  }

  // ── PID → motors ─────────────────────────────────────────────────────────
  float output = balancePID.compute(setpoint, angle, dt);
  int speed = constrain((int)output, -maxSpeed, maxSpeed);
  motors.drive(speed, steer);
}
