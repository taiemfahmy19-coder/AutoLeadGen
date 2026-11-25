import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:autoleadgen_mobile/api/api_client.dart';

class MapScreen extends StatefulWidget {
  const MapScreen({super.key});

  @override
  State<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends State<MapScreen> {
  List<Marker> _markers = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadMapData();
  }

  void _loadMapData() async {
    try {
      final geo = await ApiClient().getGeoJSON();
      final features = geo["features"] as List<dynamic>? ?? [];
      final markers = <Marker>[];

      for (final f in features) {
        final coords = f["geometry"]?["coordinates"];
        if (coords != null && coords.length >= 2) {
          final lon = (coords[0] as num).toDouble();
          final lat = (coords[1] as num).toDouble();
          final name = f["properties"]?["name"] ?? "شركة";
          markers.add(
            Marker(
              point: LatLng(lat, lon),
              width: 36,
              height: 36,
              child: GestureDetector(
                onTap: () {
                  showModalBottomSheet(
                    context: context,
                    builder: (_) => Container(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(name, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                          const SizedBox(height: 8),
                          Text("المدينة: ${f['properties']?['city'] ?? ''}"),
                          Text("النشاط: ${f['properties']?['industry'] ?? ''}"),
                          Text("الهاتف: ${f['properties']?['phone'] ?? ''}"),
                        ],
                      ),
                    ),
                  );
                },
                child: const Icon(Icons.location_on, color: Color(0xFF6366F1), size: 32),
              ),
            ),
          );
        }
      }

      if (mounted) {
        setState(() {
          _markers = markers;
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
      appBar: AppBar(title: Text("خريطة الشركات (${_markers.length})")),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : FlutterMap(
              options: const MapOptions(
                initialCenter: LatLng(30.0444, 31.2357),
                initialZoom: 6,
              ),
              children: [
                TileLayer(
                  urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                  userAgentPackageName: 'com.autoleadgen.mobile',
                ),
                MarkerLayer(markers: _markers),
              ],
            ),
    );
  }
}
