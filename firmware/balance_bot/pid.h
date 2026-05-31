#pragma once

class PID {
public:
  float kp, ki, kd;

  PID(float p, float i, float d)
    : kp(p), ki(i), kd(d), _integral(0), _prevError(0) {}

  void reset() {
    _integral = 0;
    _prevError = 0;
  }

  float compute(float setpoint, float input, float dt) {
    float error = setpoint - input;
    _integral += error * dt;
    // Anti-windup: clamp integral
    _integral = constrain(_integral, -200.0f, 200.0f);
    float derivative = (error - _prevError) / dt;
    _prevError = error;
    return kp * error + ki * _integral + kd * derivative;
  }

private:
  float _integral;
  float _prevError;
};
