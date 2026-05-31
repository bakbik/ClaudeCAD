#pragma once
#include <SoftwareSerial.h>

enum class Cmd { NONE, FORWARD, BACKWARD, LEFT, RIGHT, STOP, SPEED_UP, SPEED_DOWN };

class BluetoothCmd {
public:
  BluetoothCmd(uint8_t rxPin, uint8_t txPin)
    : _bt(rxPin, txPin) {}

  void begin(long baud = 9600) { _bt.begin(baud); }

  Cmd read() {
    if (!_bt.available()) return Cmd::NONE;
    char c = _bt.read();
    switch (c) {
      case 'F': return Cmd::FORWARD;
      case 'B': return Cmd::BACKWARD;
      case 'L': return Cmd::LEFT;
      case 'R': return Cmd::RIGHT;
      case 'S': return Cmd::STOP;
      case '+': return Cmd::SPEED_UP;
      case '-': return Cmd::SPEED_DOWN;
      default:  return Cmd::NONE;
    }
  }

private:
  SoftwareSerial _bt;
};
