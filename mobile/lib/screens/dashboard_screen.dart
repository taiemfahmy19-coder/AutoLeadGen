import 'package:flutter/material.dart';
import 'package:autoleadgen_mobile/api/api_client.dart';
import 'package:autoleadgen_mobile/screens/leads_screen.dart';
import 'package:autoleadgen_mobile/screens/discovery_screen.dart';
import 'package:autoleadgen_mobile/screens/map_screen.dart';
import 'package:autoleadgen_mobile/screens/email_screen.dart';
import 'package:autoleadgen_mobile/screens/task_screen.dart';
import 'package:autoleadgen_mobile/screens/login_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  Map<String, dynamic> _metrics = {};
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadMetrics();
  }

  void _loadMetrics() async {
    setState(() => _loading = true);
    try {
      final data = await ApiClient().getDashboardMetrics();
      if (mounted) {
        setState(() {
          _metrics = data;
          _loading = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  Widget _statCard(String title, String val, IconData icon, Color color) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF0F172A),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(title, style: const TextStyle(fontSize: 13, color: Color(0xFF94A3B8))),
              Icon(icon, color: color, size: 20),
            ],
          ),
          const SizedBox(height: 12),
          Text(val, style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: color)),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("AutoLeadGen V3"),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadMetrics,
          ),
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () async {
              await ApiClient().logout();
              if (!mounted) return;
              Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => const LoginScreen()));
            },
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: () async => _loadMetrics(),
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  Row(
                    children: [
                      const Icon(Icons.circle, size: 10, color: Color(0xFF10B981)),
                      const SizedBox(width: 8),
                      Text("متصل بالنظام: ${ApiClient().username} (${ApiClient().role})",
                          style: const TextStyle(fontSize: 12, color: Color(0xFF10B981))),
                    ],
                  ),
                  const SizedBox(height: 16),
                  GridView.count(
                    crossAxisCount: 2,
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    mainAxisSpacing: 12,
                    crossAxisSpacing: 12,
                    childAspectRatio: 1.4,
                    children: [
                      _statCard("إجمالي الشركات", "${_metrics['total'] ?? 0}", Icons.business, const Color(0xFF6366F1)),
                      _statCard("مؤهلة للتواصل", "${_metrics['ready'] ?? 0}", Icons.check_circle, const Color(0xFF10B981)),
                      _statCard("تم التواصل", "${_metrics['contacted'] ?? 0}", Icons.send, const Color(0xFF3B82F6)),
                      _statCard("ردود واردة", "${_metrics['replied'] ?? 0}", Icons.mark_email_read, const Color(0xFFF59E0B)),
                    ],
                  ),
                  const SizedBox(height: 24),
                  const Text("التحكم السريع", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white)),
                  const SizedBox(height: 12),
                  ListTile(
                    tileColor: const Color(0xFF0F172A),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    leading: const Icon(Icons.travel_explore, color: Color(0xFF6366F1)),
                    title: const Text("محرك الاكتشاف العالمي", style: TextStyle(fontWeight: FontWeight.bold)),
                    subtitle: const Text("بحث متعدد المصادر (OSM + Wikidata)"),
                    trailing: const Icon(Icons.arrow_forward_ios, size: 14),
                    onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const DiscoveryScreen())),
                  ),
                  const SizedBox(height: 8),
                  ListTile(
                    tileColor: const Color(0xFF0F172A),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    leading: const Icon(Icons.map, color: Color(0xFF10B981)),
                    title: const Text("خريطة الشركات الحقيقية", style: TextStyle(fontWeight: FontWeight.bold)),
                    subtitle: const Text("Leaflet / OpenStreetMap GPS"),
                    trailing: const Icon(Icons.arrow_forward_ios, size: 14),
                    onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const MapScreen())),
                  ),
                  const SizedBox(height: 8),
                  ListTile(
                    tileColor: const Color(0xFF0F172A),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    leading: const Icon(Icons.people, color: Color(0xFF3B82F6)),
                    title: const Text("إدارة العملاء CRM", style: TextStyle(fontWeight: FontWeight.bold)),
                    subtitle: const Text("تصفح وتحديث وتصفية الشركات"),
                    trailing: const Icon(Icons.arrow_forward_ios, size: 14),
                    onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const LeadsScreen())),
                  ),
                  const SizedBox(height: 8),
                  ListTile(
                    tileColor: const Color(0xFF0F172A),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    leading: const Icon(Icons.mail, color: Color(0xFFF59E0B)),
                    title: const Text("مركز البريد والردود", style: TextStyle(fontWeight: FontWeight.bold)),
                    subtitle: const Text("متابعة الردود وتصنيف المشاعر"),
                    trailing: const Icon(Icons.arrow_forward_ios, size: 14),
                    onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const EmailScreen())),
                  ),
                  const SizedBox(height: 8),
                  ListTile(
                    tileColor: const Color(0xFF0F172A),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    leading: const Icon(Icons.task, color: Color(0xFFA855F7)),
                    title: const Text("طابور المهام الخلفية", style: TextStyle(fontWeight: FontWeight.bold)),
                    subtitle: const Text("متابعة العمليات والإلغاء الفوري"),
                    trailing: const Icon(Icons.arrow_forward_ios, size: 14),
                    onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const TaskScreen())),
                  ),
                ],
              ),
            ),
    );
  }
}
