import 'dart:convert';
import 'dart:async';
import 'package:http/http.dart' as http;
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ApiClient {
  static final ApiClient _instance = ApiClient._internal();
  factory ApiClient() => _instance;
  ApiClient._internal();

  String baseUrl = "http://100.82.140.21:8502";
  String? token;
  String? username;
  String? role;
  WebSocketChannel? _wsChannel;
  final StreamController<Map<String, dynamic>> _eventStreamController = StreamController<Map<String, dynamic>>.broadcast();

  Stream<Map<String, dynamic>> get eventStream => _eventStreamController.stream;

  Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    baseUrl = prefs.getString("v3_server_url") ?? "http://10.0.2.2:8502";
    token = prefs.getString("v3_jwt_token");
    username = prefs.getString("v3_username");
    role = prefs.getString("v3_role");
    if (token != null) {
      _connectWebSocket();
    }
  }

  void _connectWebSocket() {
    try {
      final wsUrl = baseUrl.replaceFirst("http://", "ws://").replaceFirst("https://", "wss://");
      _wsChannel = WebSocketChannel.connect(Uri.parse("$wsUrl/ws/events?token=$token"));
      _wsChannel?.stream.listen((message) {
        try {
          final data = json.decode(message);
          _eventStreamController.add(data);
        } catch (_) {}
      }, onError: (_) {}, onDone: () {});
    } catch (_) {}
  }

  Future<bool> login(String serverUrl, String user, String password) async {
    baseUrl = serverUrl.trim().replaceAll(RegExp(r'/+$'), '');
    try {
      final response = await http.post(
        Uri.parse("$baseUrl/api/auth/login"),
        headers: {"Content-Type": "application/x-www-form-urlencoded"},
        body: {"username": user.trim(), "password": password},
      ).timeout(const Duration(seconds: 12));

      if (response.statusCode == 200) {
        final data = json.decode(utf8.decode(response.bodyBytes));
        token = data["access_token"];
        username = data["username"];
        role = data["role"];

        final prefs = await SharedPreferences.getInstance();
        await prefs.setString("v3_server_url", baseUrl);
        await prefs.setString("v3_jwt_token", token!);
        await prefs.setString("v3_username", username!);
        await prefs.setString("v3_role", role!);

        _connectWebSocket();
        return true;
      }
      return false;
    } catch (_) {
      return false;
    }
  }

  Future<void> logout() async {
    token = null;
    username = null;
    role = null;
    _wsChannel?.sink.close();
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove("v3_jwt_token");
    await prefs.remove("v3_username");
    await prefs.remove("v3_role");
  }

  Map<String, String> _headers() => {
    "Content-Type": "application/json",
    if (token != null) "Authorization": "Bearer $token",
  };

  Future<Map<String, dynamic>> getDashboardMetrics() async {
    final res = await http.get(Uri.parse("$baseUrl/api/metrics/dashboard"), headers: _headers());
    if (res.statusCode == 200) {
      return json.decode(utf8.decode(res.bodyBytes));
    }
    throw Exception("Failed to load metrics");
  }

  Future<Map<String, dynamic>> getLeads({int page = 1, int pageSize = 30, String? status, String? search}) async {
    final query = {
      "page": page.toString(),
      "page_size": pageSize.toString(),
      if (status != null && status.isNotEmpty) "status": status,
      if (search != null && search.isNotEmpty) "search": search,
    };
    final uri = Uri.parse("$baseUrl/api/leads").replace(queryParameters: query);
    final res = await http.get(uri, headers: _headers());
    if (res.statusCode == 200) {
      return json.decode(utf8.decode(res.bodyBytes));
    }
    throw Exception("Failed to load leads");
  }

  Future<Map<String, dynamic>> getGeoJSON({String? industry}) async {
    final query = {
      if (industry != null && industry.isNotEmpty) "industry": industry,
    };
    final uri = Uri.parse("$baseUrl/api/leads/geojson").replace(queryParameters: query);
    final res = await http.get(uri, headers: _headers());
    if (res.statusCode == 200) {
      return json.decode(utf8.decode(res.bodyBytes));
    }
    throw Exception("Failed to load GeoJSON");
  }

  Future<String> startDiscovery({required String country, String city = "", String businessType = "all", List<String>? sources}) async {
    final res = await http.post(
      Uri.parse("$baseUrl/api/discovery/start"),
      headers: _headers(),
      body: json.encode({
        "country": country,
        "city": city,
        "business_type": businessType,
        "sources": sources ?? ["overpass", "wikidata"],
      }),
    );
    if (res.statusCode == 200) {
      final data = json.decode(utf8.decode(res.bodyBytes));
      return data["task_id"] ?? "";
    }
    throw Exception("Failed to start discovery");
  }

  Future<List<dynamic>> getTasks() async {
    final res = await http.get(Uri.parse("$baseUrl/api/tasks"), headers: _headers());
    if (res.statusCode == 200) {
      return json.decode(utf8.decode(res.bodyBytes));
    }
    return [];
  }

  Future<bool> cancelTask(String taskId) async {
    final res = await http.post(Uri.parse("$baseUrl/api/tasks/$taskId/cancel"), headers: _headers());
    return res.statusCode == 200;
  }

  Future<List<dynamic>> getEmailInbox({int? leadId}) async {
    final uri = Uri.parse("$baseUrl/api/email/inbox");
    final res = await http.get(uri, headers: _headers());
    if (res.statusCode == 200) {
      return json.decode(utf8.decode(res.bodyBytes));
    }
    return [];
  }
}
