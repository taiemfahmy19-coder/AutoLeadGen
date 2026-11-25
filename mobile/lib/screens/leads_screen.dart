import 'package:flutter/material.dart';
import 'package:autoleadgen_mobile/api/api_client.dart';

class LeadsScreen extends StatefulWidget {
  const LeadsScreen({super.key});

  @override
  State<LeadsScreen> createState() => _LeadsScreenState();
}

class _LeadsScreenState extends State<LeadsScreen> {
  List<dynamic> _leads = [];
  int _total = 0;
  int _page = 1;
  bool _loading = true;
  final _searchCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    _fetchLeads();
  }

  void _fetchLeads() async {
    setState(() => _loading = true);
    try {
      final res = await ApiClient().getLeads(page: _page, search: _searchCtrl.text);
      if (mounted) {
        setState(() {
          _leads = res["leads"] ?? [];
          _total = res["total"] ?? 0;
          _loading = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text("قاعدة العملاء ($_total)"),
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: TextField(
              controller: _searchCtrl,
              onSubmitted: (_) {
                _page = 1;
                _fetchLeads();
              },
              decoration: InputDecoration(
                hintText: "بحث بالاسم، المدينة، الإيميل...",
                prefixIcon: const Icon(Icons.search),
                suffixIcon: IconButton(
                  icon: const Icon(Icons.send),
                  onPressed: () {
                    _page = 1;
                    _fetchLeads();
                  },
                ),
                filled: true,
                fillColor: const Color(0xFF0F172A),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
              ),
            ),
          ),
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : ListView.separated(
                    itemCount: _leads.length,
                    separatorBuilder: (_, __) => const Divider(color: Color(0x1AFFFFFF), height: 1),
                    itemBuilder: (context, idx) {
                      final l = _leads[idx];
                      return ListTile(
                        leading: CircleAvatar(
                          backgroundColor: const Color(0xFF1E293B),
                          child: Text(
                            "${l['score'] ?? 0}",
                            style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF6366F1)),
                          ),
                        ),
                        title: Text(l['business_name'] ?? "", style: const TextStyle(fontWeight: FontWeight.bold)),
                        subtitle: Text("${l['city'] ?? ''} • ${l['industry'] ?? ''} • ${l['phone'] ?? ''}"),
                        trailing: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(
                            color: const Color(0xFF1E293B),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Text(
                            l['status'] ?? "NEW",
                            style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold),
                          ),
                        ),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }
}
