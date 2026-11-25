import 'package:flutter/material.dart';
import 'package:autoleadgen_mobile/api/api_client.dart';

class DiscoveryScreen extends StatefulWidget {
  const DiscoveryScreen({super.key});

  @override
  State<DiscoveryScreen> createState() => _DiscoveryScreenState();
}

class _DiscoveryScreenState extends State<DiscoveryScreen> {
  final _countryCtrl = TextEditingController(text: "Egypt");
  final _cityCtrl = TextEditingController(text: "Cairo");
  String _businessType = "all";
  bool _running = false;
  String _activeTaskId = "";
  double _progress = 0.0;
  String _statusMsg = "";

  @override
  void initState() {
    super.initState();
    ApiClient().eventStream.listen((event) {
      if (event["event"] == "task_progress" && event["data"]?["task_id"] == _activeTaskId) {
        if (mounted) {
          setState(() {
            _progress = (event["data"]["progress"] ?? 0.0).toDouble();
            _statusMsg = event["data"]["message"] ?? "";
          });
        }
      } else if (event["event"] == "task_completed" && event["data"]?["task_id"] == _activeTaskId) {
        if (mounted) {
          setState(() {
            _running = false;
            _progress = 1.0;
            _statusMsg = "تم الانتهاء بنجاح!";
          });
        }
      }
    });
  }

  void _start() async {
    setState(() {
      _running = true;
      _progress = 0.05;
      _statusMsg = "جاري الاتصال بمصادر البيانات...";
    });

    try {
      final taskId = await ApiClient().startDiscovery(
        country: _countryCtrl.text,
        city: _cityCtrl.text,
        businessType: _businessType,
      );
      setState(() => _activeTaskId = taskId);
    } catch (e) {
      setState(() {
        _running = false;
        _statusMsg = "خطأ: $e";
      });
    }
  }

  void _stop() async {
    if (_activeTaskId.isNotEmpty) {
      await ApiClient().cancelTask(_activeTaskId);
      setState(() {
        _running = false;
        _statusMsg = "تم إرسال طلب الإيقاف.";
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("محرك الاكتشاف العالمي")),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            TextField(
              controller: _countryCtrl,
              decoration: const InputDecoration(labelText: "الدولة (مثال: Egypt, UAE, Saudi Arabia)", filled: true),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _cityCtrl,
              decoration: const InputDecoration(labelText: "المدينة (اختياري)", filled: true),
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              value: _businessType,
              items: const [
                DropdownMenuItem(value: "all", child: Text("كل الأنشطة التجارية")),
                DropdownMenuItem(value: "restaurant", child: Text("مطاعم وكافيهات")),
                DropdownMenuItem(value: "clinic", child: Text("عيادات ومراكز طبية")),
                DropdownMenuItem(value: "shop", child: Text("متاجر ومحلات")),
                DropdownMenuItem(value: "hotel", child: Text("فنادق وسياحة")),
                DropdownMenuItem(value: "office", child: Text("مكاتب وشركات")),
              ],
              onChanged: (v) => setState(() => _businessType = v ?? "all"),
              decoration: const InputDecoration(labelText: "نوع النشاط", filled: true),
            ),
            const SizedBox(height: 24),
            if (_running) ...[
              LinearProgressIndicator(value: _progress > 0 ? _progress : null),
              const SizedBox(height: 10),
              Text(_statusMsg, style: const TextStyle(fontSize: 13, color: Color(0xFF94A3B8))),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                style: ElevatedButton.styleFrom(backgroundColor: Colors.redAccent),
                onPressed: _stop,
                icon: const Icon(Icons.stop),
                label: const Text("إيقاف البحث"),
              ),
            ] else ...[
              SizedBox(
                width: double.infinity,
                height: 48,
                child: ElevatedButton.icon(
                  style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF6366F1)),
                  onPressed: _start,
                  icon: const Icon(Icons.search),
                  label: const Text("بدء الاكتشاف عبر المصادر المفتوحة"),
                ),
              ),
              if (_statusMsg.isNotEmpty) ...[
                const SizedBox(height: 12),
                Text(_statusMsg, style: const TextStyle(color: Color(0xFF10B981))),
              ]
            ],
          ],
        ),
      ),
    );
  }
}
