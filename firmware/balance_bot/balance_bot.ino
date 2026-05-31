/*
 * Self-Balancing Robot Firmware
 *
 * Hardware:
 *   MPU-6050  → SDA=A4, SCL=A5
 *   L298N     → ENA=9, IN1=7, IN2=6, ENB=3, IN3=5, IN4=4
 *   HC-05/06  → RX=10, TX=11 (SoftwareSerial)
 *
 * PID starting values: Kp=30, Ki=0, Kd=1.5
 * Tune Kp until robot oscillates, then halve it. Add Kd to dampen.
 * Ki only needed if robot drifts slowly one direction.
 */

#include <Wire.h>
#include "pid.h"
#include "motor_control.h"
#include "bluetooth_cmd.h"

// ── Pin definitions ─────────────────────────────────────────────────────────
#define BT_RX       10
#define BT_TX       11
#define ENA          9
#define IN1          7
#define IN2          6
#define ENB          3
#define IN3          5
#define IN4          4

// MPU-6050 register addresses
#define MPU_ADDR    0x68
#define PWR_MGMT_1  0x6B
#define ACCEL_XOUT  0x3B
#define GYRO_XOUT   0x43

// ── Tuning constants (adjust these) ─────────────────────────────────────────
float KP            = 30.0f;
float KI            =  0.0f;
float KD            =  1.5f;
float BALANCE_ANGLE =  0.0f;   // degrees; adjust if CoM is off-center
int   MAX_SPEED     =  200;    // 0–255 PWM ceiling
float COMP_ALPHA    =  0.98f;  // complementary filter weight toward gyro

// ── Steer bias from BT commands ──────────────────────────────────────────────
int steerBias  = 0;   // -80..+80 injected into drive()
float angleTrim = 0;  // degrees forward/backward lean from phone

// ── Objects ──────────────────────────────────────────────────────────────────
PID         pid(KP, KI, KD);
DualMotor   motors({ENA, IN1, IN2}, {ENB, IN3, IN4});
BluetoothCmd bt(BT_RX, BT_TX);

// ── State ────────────────────────────────────────────────────────────────────
float angle    = 0;
bool  fallen   = false;
unsigned long lastTime = 0;

// ── MPU-6050 raw read ────────────────────────────────────────────────────────
struct ImuData { int16_t ax, ay, az, gx, gy, gz; };

ImuData readMPU() {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(ACCEL_XOUT);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_ADDR, 14, true);
  ImuData d;
  d.ax = Wire.read() << 8 | Wire.read();
  d.ay = Wire.read() << 8 | Wire.read();
  d.az = Wire.read() << 8 | Wire.read();
  Wire.read(); Wire.read(); // skip temperature
  d.gx = Wire.read() << 8 | Wire.read();
  d.gy = Wire.read() << 8 | Wire.read();
  d.gz = Wire.read() << 8 | Wire.read();
  return d;
}

void setup() {
  Serial.begin(115200);
  Wire.begin();

  // Wake MPU-6050
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(PWR_MGMT_1);
  Wire.write(0);
  Wire.endTransmission(true);
  delay(100);

  motors.begin();
  bt.begin(9600);

  // Warm up filter with 200 readings
  for (int i = 0; i < 200; i++) {
    ImuData d = readMPU();
    float accelAngle = atan2((float)d.ay, (float)d.az) * 180.0f / PI;
    angle = COMP_ALPHA * angle + (1 - COMP_ALPHA) * accelAngle;
    delay(5);
  }
  lastTime = millis();
}

void loop() {
  // ── Handle BT commands ────────────────────────────────────────────────────
  Cmd cmd = bt.read();
  const float LEAN = 3.0f;
  const int   STEER = 60;
  switch (cmd) {
    case Cmd::FORWARD:    angleTrim = -LEAN; steerBias = 0;      break;
    case Cmd::BACKWARD:   angleTrim =  LEAN; steerBias = 0;      break;
    case Cmd::LEFT:       steerBias = -STEER;                    break;
    case Cmd::RIGHT:      steerBias =  STEER;                    break;
    case Cmd::STOP:       angleTrim = 0;     steerBias = 0;      break;
    case Cmd::SPEED_UP:   MAX_SPEED = min(255, MAX_SPEED + 10);  break;
    case Cmd::SPEED_DOWN: MAX_SPEED = max(50,  MAX_SPEED - 10);  break;
    default: break;
  }

  // ── Read IMU + complementary filter ──────────────────────────────────────
  unsigned long now = millis();
  float dt = (now - lastTime) / 1000.0f;
  if (dt < 0.005f) return;   // cap at ~200 Hz
  lastTime = now;

  ImuData d = readMPU();
  float accelAngle = atan2((float)d.ay, (float)d.az) * 180.0f / PI;
  float gyroRate   = (float)d.gx / 131.0f;  // deg/s at ±250°/s range
  angle = COMP_ALPHA * (angle + gyroRate * dt) + (1 - COMP_ALPHA) * accelAngle;

  // ── Fallen-over detection ─────────────────────────────────────────────────
  if (abs(angle) > 45.0f) {
    if (!fallen) { motors.stop(); pid.reset(); fallen = true; }
    return;
  }
  fallen = false;

  // ── PID → motor output ────────────────────────────────────────────────────
  float setpoint = BALANCE_ANGLE + angleTrim;
  float output   = pid.compute(setpoint, angle, dt);
  output = constrain(output, -MAX_SPEED, MAX_SPEED);

  motors.drive((int)output, steerBias);

  // ── Debug over USB serial ─────────────────────────────────────────────────
  Serial.print(angle, 2);
  Serial.print('\t');
  Serial.println(output, 1);
}
