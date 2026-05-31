import 'package:flutter/material.dart';
import '../services/bluetooth_service.dart';

class ControllerScreen extends StatefulWidget {
  final BluetoothService bt;
  final String deviceName;
  const ControllerScreen({super.key, required this.bt, required this.deviceName});

  @override
  State<ControllerScreen> createState() => _ControllerScreenState();
}

class _ControllerScreenState extends State<ControllerScreen> {
  String _activeCmd = '';

  void _send(String cmd) {
    if (cmd == _activeCmd) return;
    widget.bt.send(cmd);
    setState(() => _activeCmd = cmd);
  }

  void _release() {
    widget.bt.send('S');
    setState(() => _activeCmd = '');
  }

  Widget _dpadBtn(IconData icon, String cmd) {
    final active = _activeCmd == cmd;
    return GestureDetector(
      onTapDown: (_) => _send(cmd),
      onTapUp: (_) => _release(),
      onTapCancel: _release,
      child: Container(
        width: 80, height: 80,
        decoration: BoxDecoration(
          color: active ? Theme.of(context).colorScheme.primary : Colors.grey.shade800,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Icon(icon, color: Colors.white, size: 36),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey.shade900,
      appBar: AppBar(
        title: Text(widget.deviceName),
        backgroundColor: Colors.grey.shade850,
        actions: [
          IconButton(
            icon: const Icon(Icons.bluetooth_disabled),
            onPressed: () async {
              await widget.bt.disconnect();
              if (!mounted) return;
              Navigator.pop(context);
            },
          ),
        ],
      ),
      body: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          // D-pad
          _dpadBtn(Icons.arrow_upward, 'F'),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              _dpadBtn(Icons.arrow_back, 'L'),
              const SizedBox(width: 8),
              GestureDetector(
                onTap: _release,
                child: Container(
                  width: 80, height: 80,
                  decoration: BoxDecoration(
                    color: Colors.red.shade700,
                    borderRadius: BorderRadius.circular(40),
                  ),
                  child: const Icon(Icons.stop, color: Colors.white, size: 36),
                ),
              ),
              const SizedBox(width: 8),
              _dpadBtn(Icons.arrow_forward, 'R'),
            ],
          ),
          const SizedBox(height: 8),
          _dpadBtn(Icons.arrow_downward, 'B'),
          const SizedBox(height: 40),
          // Speed controls
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Text('Speed', style: TextStyle(color: Colors.white)),
              const SizedBox(width: 16),
              IconButton(
                icon: const Icon(Icons.remove_circle_outline, color: Colors.white),
                onPressed: () => widget.bt.send('-'),
              ),
              IconButton(
                icon: const Icon(Icons.add_circle_outline, color: Colors.white),
                onPressed: () => widget.bt.send('+'),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
