import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:aupat_mobile/models/location_model.dart';
import 'package:flutter/foundation.dart';
import 'package:path/path.dart' as path;

/// HTTP API client for AUPAT Core backend
/// Handles all REST API communication with desktop server
class AupatApiClient {
  static const String _defaultBaseUrl = 'http://localhost:5002';
  static const String _prefKeyBaseUrl = 'api_base_url';
  static const Duration _timeout = Duration(seconds: 30);

  String? _baseUrl;

  /// Get configured API base URL
  Future<String> getBaseUrl() async {
    if (_baseUrl != null) return _baseUrl!;

    final prefs = await SharedPreferences.getInstance();
    _baseUrl = prefs.getString(_prefKeyBaseUrl) ?? _defaultBaseUrl;
    return _baseUrl!;
  }

  /// Set API base URL (for settings)
  Future<void> setBaseUrl(String url) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_prefKeyBaseUrl, url);
    _baseUrl = url;
  }

  /// Health check endpoint
  /// Returns true if API is reachable and healthy
  Future<bool> healthCheck() async {
    try {
      final baseUrl = await getBaseUrl();
      final response = await http.get(
        Uri.parse('$baseUrl/api/health'),
      ).timeout(_timeout);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return data['status'] == 'ok';
      }
      return false;
    } catch (e) {
      debugPrint('Health check failed: $e');
      return false;
    }
  }

  /// Push pending locations to desktop
  /// POST /api/sync/mobile
  Future<Map<String, dynamic>> pushLocations(
    List<PendingSyncLocation> locations,
  ) async {
    try {
      final baseUrl = await getBaseUrl();
      final deviceId = await _getDeviceId();

      // Convert locations and encode photos to base64
      final newLocationsList = <Map<String, dynamic>>[];
      for (final loc in locations) {
        final photoData = <Map<String, String>>[];

        // Encode each photo to base64
        for (final photoPath in loc.photos) {
          try {
            final file = File(photoPath);
            if (await file.exists()) {
              final bytes = await file.readAsBytes();
              final base64Data = base64Encode(bytes);
              final filename = path.basename(photoPath);

              photoData.add({
                'filename': filename,
                'data': base64Data,
              });
            }
          } catch (e) {
            debugPrint('Failed to encode photo $photoPath: $e');
          }
        }

        newLocationsList.add({
          'loc_uuid': loc.locUuid,
          'loc_name': loc.locName,
          'lat': loc.lat,
          'lon': loc.lon,
          'loc_type': loc.locType,
          'created_at': loc.createdAt,
          'photos': photoData,
        });
      }

      final payload = {
        'device_id': deviceId,
        'new_locations': newLocationsList,
        'updated_locations': [],
        'device_timestamp': DateTime.now().toIso8601String(),
      };

      debugPrint('Pushing ${locations.length} locations to desktop');

      final response = await http.post(
        Uri.parse('$baseUrl/api/sync/mobile'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(payload),
      ).timeout(_timeout);

      if (response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      } else {
        return {
          'status': 'error',
          'error': 'HTTP ${response.statusCode}: ${response.body}',
        };
      }
    } catch (e) {
      debugPrint('Push locations failed: $e');
      return {
        'status': 'error',
        'error': e.toString(),
      };
    }
  }

  /// Pull new locations from desktop
  /// GET /api/sync/mobile/pull?since=...
  Future<List<Location>> pullLocations({DateTime? since}) async {
    try {
      final baseUrl = await getBaseUrl();
      final sinceParam = since?.toIso8601String() ?? '';

      final uri = Uri.parse('$baseUrl/api/sync/mobile/pull').replace(
        queryParameters: sinceParam.isNotEmpty ? {'since': sinceParam} : {},
      );

      debugPrint('Pulling locations from desktop since $sinceParam');

      final response = await http.get(uri).timeout(_timeout);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        final locations = (data['locations'] as List<dynamic>?) ?? [];

        return locations.map((json) => Location.fromJson(json as Map<String, dynamic>)).toList();
      } else {
        debugPrint('Pull failed: HTTP ${response.statusCode}');
        return [];
      }
    } catch (e) {
      debugPrint('Pull locations failed: $e');
      return [];
    }
  }

  /// Upload photo to backend
  /// POST /api/import/images
  /// Returns immich_asset_id on success
  Future<String?> uploadPhoto(
    String filePath,
    String locUuid,
  ) async {
    try {
      final baseUrl = await getBaseUrl();
      final uri = Uri.parse('$baseUrl/api/import/images');

      final request = http.MultipartRequest('POST', uri);
      request.files.add(await http.MultipartFile.fromPath('image', filePath));
      request.fields['loc_uuid'] = locUuid;

      debugPrint('Uploading photo: $filePath');

      final response = await request.send().timeout(_timeout);
      final responseBody = await response.stream.bytesToString();

      if (response.statusCode == 200) {
        final data = jsonDecode(responseBody) as Map<String, dynamic>;
        return data['immich_asset_id'] as String?;
      } else {
        debugPrint('Upload failed: HTTP ${response.statusCode}');
        return null;
      }
    } catch (e) {
      debugPrint('Upload photo failed: $e');
      return null;
    }
  }

  /// Get device ID (unique identifier for this mobile device)
  Future<String> _getDeviceId() async {
    final prefs = await SharedPreferences.getInstance();
    String? deviceId = prefs.getString('device_id');

    if (deviceId == null) {
      // Generate new device ID
      deviceId = 'mobile-${DateTime.now().millisecondsSinceEpoch}';
      await prefs.setString('device_id', deviceId);
    }

    return deviceId;
  }

  /// Test API connection with full details
  Future<Map<String, dynamic>> testConnection() async {
    try {
      final baseUrl = await getBaseUrl();
      final startTime = DateTime.now();

      final response = await http.get(
        Uri.parse('$baseUrl/api/health'),
      ).timeout(_timeout);

      final duration = DateTime.now().difference(startTime);

      return {
        'success': response.statusCode == 200,
        'status_code': response.statusCode,
        'response_time_ms': duration.inMilliseconds,
        'base_url': baseUrl,
        'error': response.statusCode != 200 ? response.body : null,
      };
    } catch (e) {
      return {
        'success': false,
        'error': e.toString(),
        'base_url': await getBaseUrl(),
      };
    }
  }
}
