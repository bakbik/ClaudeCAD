import 'package:flutter/material.dart';
import 'package:flutter_bluetooth_serial/flutter_bluetooth_serial.dart';
import '../services/bluetooth_service.dart';
import 'controller_screen.dart';

class DeviceListScreen extends StatefulWidget {
  final BluetoothService bt;
  const DeviceListScreen({super.key, required this.bt});

  @override
  State<DeviceListScreen> createState() => _DeviceListScreenState();
}

class _DeviceListScreenState extends State<DeviceListScreen> {
  List<BluetoothDevice> _devices = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadDevices();
  }

  Future<void> _loadDevices() async {
    final devices = await widget.bt.pairedDevices();
    setState(() { _devices = devices; _loading = false; });
  }

  Future<void> _connect(BluetoothDevice device) async {
    try {
      await widget.bt.connect(device);
      if (!mounted) return;
      Navigator.pushReplacement(context, MaterialPageRoute(
        builder: (_) => ControllerScreen(bt: widget.bt, deviceName: device.name ?? device.address),
      ));
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Connection failed: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Select Robot'),
        actions: [IconButton(icon: const Icon(Icons.refresh), onPressed: _loadDevices)],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _devices.isEmpty
              ? const Center(child: Text('No paired devices.\nPair HC-05 in Android Settings first.', textAlign: TextAlign.center))
              : ListView.builder(
                  itemCount: _devices.length,
                  itemBuilder: (_, i) => ListTile(
                    leading: const Icon(Icons.bluetooth),
                    title: Text(_devices[i].name ?? 'Unknown'),
                    subtitle: Text(_devices[i].address),
                    onTap: () => _connect(_devices[i]),
                  ),
                ),
    );
  }
}
