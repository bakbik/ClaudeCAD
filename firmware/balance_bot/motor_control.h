#pragma once
#include <Arduino.h>

// L298N dual H-bridge driver
// ENA/ENB are PWM speed pins; IN1-4 set direction
struct MotorPins {
  uint8_t en, in1, in2;
};

class DualMotor {
public:
  DualMotor(MotorPins left, MotorPins right)
    : _left(left), _right(right) {}

  void begin() {
    for (auto& m : {_left, _right}) {
      pinMode(m.en, OUTPUT);
      pinMode(m.in1, OUTPUT);
      pinMode(m.in2, OUTPUT);
    }
    stop();
  }

  // speed: -255..255, positive = forward
  // steer: -255..255, positive = turn right (slow left motor)
  void drive(int speed, int steer) {
    int l = constrain(speed + steer, -255, 255);
    int r = constrain(speed - steer, -255, 255);
    _set(_left, l);
    _set(_right, r);
  }

  void stop() {
    _set(_left, 0);
    _set(_right, 0);
  }

private:
  MotorPins _left, _right;

  void _set(const MotorPins& m, int spd) {
    if (spd > 0) {
      digitalWrite(m.in1, HIGH);
      digitalWrite(m.in2, LOW);
    } else if (spd < 0) {
      digitalWrite(m.in1, LOW);
      digitalWrite(m.in2, HIGH);
    } else {
      digitalWrite(m.in1, LOW);
      digitalWrite(m.in2, LOW);
    }
    analogWrite(m.en, abs(spd));
  }
};
