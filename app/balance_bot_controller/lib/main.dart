import 'package:flutter/material.dart';
import 'services/bluetooth_service.dart';
import 'screens/device_list_screen.dart';

void main() => runApp(const BalanceBotApp());

class BalanceBotApp extends StatelessWidget {
  const BalanceBotApp({super.key});

  @override
  Widget build(BuildContext context) {
    final bt = BluetoothService();
    return MaterialApp(
      title: 'Balance Bot',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.deepOrange,
          brightness: Brightness.dark,
        ),
        useMaterial3: true,
      ),
      home: DeviceListScreen(bt: bt),
    );
  }
}
