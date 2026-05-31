# Self-Balancing Robot

Two-wheeled inverted-pendulum robot controlled from an Android phone over Bluetooth Classic.

---

## Bill of Materials

| Qty | Part | Notes |
|-----|------|-------|
| 1 | Arduino Uno or Nano | Any 5V ATmega328 board |
| 2 | Yellow TT gear motor + wheel | 1:48 or 1:120 ratio, 65mm wheels |
| 1 | MPU-6050 breakout | GY-521 blue board (~$2) |
| 1 | L298N dual H-bridge module | 43×43mm variant |
| 1 | HC-05 or HC-06 Bluetooth module | HC-06 is simpler (slave-only) |
| 2 | 18650 Li-ion cell (≥2000mAh) | Or 2S LiPo 7.4V ≥1000mAh |
| 1 | 18650 dual battery holder | With JST or bare leads |
| 4 | M3×40mm standoffs + M3 nuts | Brass preferred |
| — | M3×6 screws | Mount boards to plates |
| — | Jumper wires | Female-female and male-female |
| — | 100µF 16V capacitor × 2 | Across each motor terminal |

---

## Wiring

```
                    +--[100µF]--[Motor L]
Battery (7.4V) --> L298N
                    +--[100µF]--[Motor R]
                    |
                   12V input
                    5V output --> Arduino Vin (or separate 5V reg)

MPU-6050:
  VCC --> 3.3V (Nano) or 5V (Uno)
  GND --> GND
  SDA --> A4
  SCL --> A5

HC-05/06:
  VCC --> 5V
  GND --> GND
  TX  --> D10 (Arduino RX)
  RX  --> D11 via 1kΩ voltage divider to GND (HC-05 RX is 3.3V tolerant but add divider to be safe)

L298N:
  ENA --> D9  (PWM)
  IN1 --> D7
  IN2 --> D6
  IN3 --> D5
  IN4 --> D4
  ENB --> D3  (PWM)
```

### Pin Summary

| Signal | Arduino Pin |
|--------|-------------|
| MPU SDA | A4 |
| MPU SCL | A5 |
| L298N ENA | D9 |
| L298N IN1 | D7 |
| L298N IN2 | D6 |
| L298N IN3 | D5 |
| L298N IN4 | D4 |
| L298N ENB | D3 |
| BT RX (HC-05 TX) | D10 |
| BT TX (HC-05 RX) | D11 |

---

## Arduino Setup

1. Install [Arduino IDE 2.x](https://www.arduino.cc/en/software)
2. Open `firmware/balance_bot/balance_bot.ino`
3. No extra libraries needed — uses Wire (built-in) and SoftwareSerial (built-in)
4. Select board: **Arduino Nano** (or Uno)
5. Upload

---

## Android App

Requirements: Flutter 3.x, Android SDK

```bash
cd app/balance_bot_controller
flutter pub get
flutter build apk --release
# APK: build/app/outputs/flutter-apk/app-release.apk
```

Or open the project in Android Studio and run directly on a device.

**Before connecting:** go to Android Bluetooth Settings → pair the HC-05 (PIN: `1234` or `0000`). Then open the app, select the device, and use the D-pad.

---

## 3D Printable Chassis

```bash
cd cad
pip install cadquery
python3 chassis.py
# Outputs: chassis_bottom.stl, chassis_top.stl, chassis_assembly.step
```

Print both plates in PLA or PETG:
- Layer height: 0.2mm
- Perimeters: 3
- Infill: 40%
- No supports needed

Assemble with 4× M3×40mm standoffs between plates. Motors press into side pockets and secure with M3×6 screws through the motor tabs.

---

## PID Tuning

Open the Arduino Serial Monitor at **115200 baud**. It prints `angle    output` every loop.

The robot must be able to stand freely (you may need to hold it at first).

1. Start with `KP=30, KI=0, KD=0` in `balance_bot.ino`
2. Power on while holding robot upright. Release briefly.
3. If it falls forward fast → lower Kp. Falls backward → lower Kp.
4. If it oscillates and falls → you're close. Halve Kp.
5. Add `KD=1.5` to dampen oscillation. Increase until oscillation stops.
6. Only add Ki if the robot slowly drifts in one direction over time. Keep it tiny (0.1–1.0).
7. Adjust `BALANCE_ANGLE` (±2°) if the robot leans when trying to balance — this corrects for an off-centre battery or mounting.

Typical working values: `Kp=25–40, Ki=0–2, Kd=1–3`

---

## Project Structure

```
firmware/balance_bot/
  balance_bot.ino    main sketch
  pid.h              PID controller
  motor_control.h    L298N dual motor driver
  bluetooth_cmd.h    HC-05 serial command parser

app/balance_bot_controller/
  lib/main.dart
  lib/screens/device_list_screen.dart
  lib/screens/controller_screen.dart
  lib/services/bluetooth_service.dart

cad/
  chassis.py          CadQuery parametric chassis
  chassis_bottom.stl  Print this (motor + battery plate)
  chassis_top.stl     Print this (electronics plate)
  chassis_assembly.step  Full assembly preview
```
