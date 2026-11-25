import 'package:flutter/material.dart';
import 'package:autoleadgen_mobile/api/api_client.dart';
import 'package:autoleadgen_mobile/screens/login_screen.dart';
import 'package:autoleadgen_mobile/screens/dashboard_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final api = ApiClient();
  await api.init();
  runApp(const AutoLeadGenApp());
}

class AutoLeadGenApp extends StatelessWidget {
  const AutoLeadGenApp({super.key});

  @override
  Widget build(BuildContext context) {
    final api = ApiClient();
    final isLoggedIn = api.token != null;

    return MaterialApp(
      title: 'AutoLeadGen V3',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF070B14),
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFF6366F1),
          secondary: Color(0xFF8B5CF6),
          surface: Color(0xFF0F172A),
          error: Color(0xFFEF4444),
        ),
        cardTheme: const CardTheme(
          color: Color(0xFF0F172A),
          elevation: 4,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.all(Radius.circular(16)),
            side: BorderSide(color: Color(0x2A6366F1), width: 1),
          ),
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF0B1120),
          elevation: 0,
          centerTitle: true,
          titleTextStyle: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white),
        ),
        fontFamily: 'Roboto',
      ),
      home: isLoggedIn ? const DashboardScreen() : const LoginScreen(),
    );
  }
}
