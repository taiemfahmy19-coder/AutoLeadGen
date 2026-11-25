import 'package:flutter/material.dart';
import 'package:autoleadgen_mobile/api/api_client.dart';

class TaskScreen extends StatefulWidget {
  const TaskScreen({super.key});

  @override
  State<TaskScreen> createState() => _TaskScreenState();
}

class _TaskScreenState extends State<TaskScreen> {
  List<dynamic> _tasks = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _fetch();
  }

  void _fetch() async {
    setState(() => _loading = true);
    final tasks = await ApiClient().getTasks();
    if (mounted) {
      setState(() {
        _tasks = tasks;
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("طابور المهام الخلفية"),
        actions: [IconButton(icon: const Icon(Icons.refresh), onPressed: _fetch)],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _tasks.isEmpty
              ? const Center(child: Text("لا توجد مهام نشطة"))
              : ListView.builder(
                  itemCount: _tasks.length,
                  itemBuilder: (context, idx) {
                    final t = _tasks[idx];
                    final isRunning = t["status"] == "running";
                    return Card(
                      margin: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                      child: ListTile(
                        leading: Icon(
                          isRunning ? Icons.hourglass_top : Icons.done_all,
                          color: isRunning ? const Color(0xFFF59E0B) : const Color(0xFF10B981),
                        ),
                        title: Text("${t['task_type']} (${t['id']})", style: const TextStyle(fontWeight: FontWeight.bold)),
                        subtitle: Text("الحالة: ${t['status']} • التقدم: ${(t['progress'] * 100).toInt()}%"),
                        trailing: isRunning
                            ? IconButton(
                                icon: const Icon(Icons.cancel, color: Colors.redAccent),
                                onPressed: () async {
                                  await ApiClient().cancelTask(t["id"]);
                                  _fetch();
                                },
                              )
                            : null,
                      ),
                    );
                  },
                ),
    );
  }
}
