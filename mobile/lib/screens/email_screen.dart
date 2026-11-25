import 'package:flutter/material.dart';
import 'package:autoleadgen_mobile/api/api_client.dart';

class EmailScreen extends StatefulWidget {
  const EmailScreen({super.key});

  @override
  State<EmailScreen> createState() => _EmailScreenState();
}

class _EmailScreenState extends State<EmailScreen> {
  List<dynamic> _messages = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _fetch();
  }

  void _fetch() async {
    setState(() => _loading = true);
    final msgs = await ApiClient().getEmailInbox();
    if (mounted) {
      setState(() {
        _messages = msgs;
        _loading = false;
      });
    }
  }

  Color _sentimentColor(String s) {
    switch (s.toLowerCase()) {
      case "interested": return const Color(0xFF10B981);
      case "not_interested": return const Color(0xFFEF4444);
      case "out_of_office": return const Color(0xFFF59E0B);
      case "follow_up": return const Color(0xFF3B82F6);
      default: return Colors.grey;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("صندوق الردود الذكي")),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _messages.isEmpty
              ? const Center(child: Text("لا توجد رسائل واردة بعد"))
              : ListView.separated(
                  itemCount: _messages.length,
                  separatorBuilder: (_, __) => const Divider(color: Color(0x1AFFFFFF), height: 1),
                  itemBuilder: (context, idx) {
                    final m = _messages[idx];
                    final sentiment = m["sentiment"] ?? "unknown";
                    return ListTile(
                      title: Text(m["subject"] ?? "بدون عنوان", style: const TextStyle(fontWeight: FontWeight.bold)),
                      subtitle: Text("من: ${m['from_addr'] ?? ''}\n${m['body_text'] ?? ''}", maxLines: 2),
                      trailing: Chip(
                        label: Text(sentiment, style: const TextStyle(fontSize: 10, color: Colors.white)),
                        backgroundColor: _sentimentColor(sentiment),
                      ),
                    );
                  },
                ),
    );
  }
}
