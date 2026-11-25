import 'package:flutter/material.dart';
import 'package:autoleadgen_mobile/api/api_client.dart';
import 'package:autoleadgen_mobile/screens/dashboard_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _serverCtrl = TextEditingController(text: "http://100.82.140.21:8502");
  final _userCtrl = TextEditingController(text: "admin");
  final _passCtrl = TextEditingController(text: "admin123");
  bool _isLoading = false;
  String? _errorMsg;

  void _doLogin() async {
    setState(() {
      _isLoading = true;
      _errorMsg = null;
    });

    final ok = await ApiClient().login(
      _serverCtrl.text,
      _userCtrl.text,
      _passCtrl.text,
    );

    if (!mounted) return;
    setState(() => _isLoading = false);

    if (ok) {
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (_) => const DashboardScreen()),
      );
    } else {
      setState(() {
        _errorMsg = "فشل الاتصال بالخادم. يرجى التأكد من تشغيل Start_V3_API.bat والـ Tailscale IP.";
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 28),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                width: 72,
                height: 72,
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFF6366F1), Color(0xFFA855F7)],
                  ),
                  borderRadius: BorderRadius.circular(20),
                  boxShadow: [
                    BoxShadow(
                      color: const Color(0xFF6366F1).withOpacity(0.4),
                      blurRadius: 24,
                    ),
                  ],
                ),
                child: const Icon(Icons.hub_rounded, size: 40, color: Colors.white),
              ),
              const SizedBox(height: 20),
              const Text(
                "AutoLeadGen V3",
                style: TextStyle(fontSize: 26, fontWeight: FontWeight.bold, color: Colors.white),
              ),
              const SizedBox(height: 6),
              const Text(
                "Global Discovery & Remote Control",
                style: TextStyle(fontSize: 13, color: Color(0xFF94A3B8)),
              ),
              const SizedBox(height: 36),
              if (_errorMsg != null)
                Container(
                  margin: const EdgeInsets.only(bottom: 16),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: const Color(0x33EF4444),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.Border.all(color: Colors.redAccent.withOpacity(0.5)),
                  ),
                  child: Text(_errorMsg!, style: const TextStyle(color: Colors.redAccent, fontSize: 13)),
                ),
              TextField(
                controller: _serverCtrl,
                decoration: InputDecoration(
                  labelText: "Server URL (Tailscale IP)",
                  prefixIcon: const Icon(Icons.router, color: Color(0xFF6366F1)),
                  filled: true,
                  fillColor: const Color(0xFF0F172A),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _userCtrl,
                decoration: InputDecoration(
                  labelText: "اسم المستخدم",
                  prefixIcon: const Icon(Icons.person, color: Color(0xFF6366F1)),
                  filled: true,
                  fillColor: const Color(0xFF0F172A),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _passCtrl,
                obscureText: true,
                decoration: InputDecoration(
                  labelText: "كلمة المرور",
                  prefixIcon: const Icon(Icons.lock, color: Color(0xFF6366F1)),
                  filled: true,
                  fillColor: const Color(0xFF0F172A),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                ),
              ),
              const SizedBox(height: 28),
              SizedBox(
                width: double.infinity,
                height: 52,
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF6366F1),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                  ),
                  onPressed: _isLoading ? null : _doLogin,
                  child: _isLoading
                      ? const CircularProgressIndicator(color: Colors.white)
                      : const Text("تسجيل الدخول والتحكم", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
