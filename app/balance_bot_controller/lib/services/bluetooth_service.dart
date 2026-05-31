import 'dart:typed_data';
import 'package:flutter_bluetooth_serial/flutter_bluetooth_serial.dart';

class BluetoothService {
  BluetoothConnection? _connection;

  bool get isConnected => _connection?.isConnected ?? false;

  Future<List<BluetoothDevice>> pairedDevices() =>
      FlutterBluetoothSerial.instance.getBondedDevices();

  Future<void> connect(BluetoothDevice device) async {
    _connection = await BluetoothConnection.toAddress(device.address);
  }

  void send(String command) {
    if (!isConnected) return;
    _connection!.output.add(Uint8List.fromList(command.codeUnits));
  }

  Future<void> disconnect() async {
    await _connection?.close();
    _connection = null;
  }
}
