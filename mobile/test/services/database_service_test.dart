import 'package:flutter_test/flutter_test.dart';
import 'package:aupat_mobile/services/database_service.dart';
import 'package:aupat_mobile/models/location_model.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'package:uuid/uuid.dart';

/// Unit tests for DatabaseService
/// Tests offline SQLite operations

void main() {
  // Initialize FFI for testing
  setUpAll(() {
    sqfliteFfiInit();
    databaseFactory = databaseFactoryFfi;
  });

  late DatabaseService dbService;

  setUp(() async {
    dbService = DatabaseService();
    // Use in-memory database for testing
    await dbService.database;
  });

  tearDown(() async {
    await dbService.clearAllData();
    await dbService.close();
  });

  group('Location CRUD Operations', () {
    test('Insert and retrieve location', () async {
      final location = Location(
        locUuid: const Uuid().v4(),
        locName: 'Test Factory',
        lat: 42.8142,
        lon: -73.9396,
        locType: 'factory',
        synced: 1,
      );

      await dbService.upsertLocation(location);

      final retrieved = await dbService.getLocation(location.locUuid);

      expect(retrieved, isNotNull);
      expect(retrieved!.locName, equals('Test Factory'));
      expect(retrieved.lat, equals(42.8142));
      expect(retrieved.lon, equals(-73.9396));
    });

    test('Get all locations returns all inserted', () async {
      final locations = [
        Location(
          locUuid: const Uuid().v4(),
          locName: 'Factory A',
          lat: 42.0,
          lon: -73.0,
          locType: 'factory',
        ),
        Location(
          locUuid: const Uuid().v4(),
          locName: 'Mill B',
          lat: 42.1,
          lon: -73.1,
          locType: 'mill',
        ),
      ];

      for (final loc in locations) {
        await dbService.upsertLocation(loc);
      }

      final allLocations = await dbService.getAllLocations();

      expect(allLocations.length, equals(2));
    });

    test('Search locations by name', () async {
      await dbService.upsertLocation(Location(
        locUuid: const Uuid().v4(),
        locName: 'Abandoned Factory',
        lat: 42.0,
        lon: -73.0,
        locType: 'factory',
      ));

      await dbService.upsertLocation(Location(
        locUuid: const Uuid().v4(),
        locName: 'Old Mill',
        lat: 42.1,
        lon: -73.1,
        locType: 'mill',
      ));

      final results = await dbService.searchLocations('Factory');

      expect(results.length, equals(1));
      expect(results.first.locName, equals('Abandoned Factory'));
    });

    test('Get locations nearby', () async {
      // Insert locations
      await dbService.upsertLocation(Location(
        locUuid: const Uuid().v4(),
        locName: 'Nearby Location',
        lat: 42.8142,
        lon: -73.9396,
        locType: 'factory',
      ));

      await dbService.upsertLocation(Location(
        locUuid: const Uuid().v4(),
        locName: 'Far Location',
        lat: 45.0,  // Much farther north
        lon: -75.0,
        locType: 'factory',
      ));

      // Search within 10km of Albany
      final nearby = await dbService.getLocationsNearby(42.8142, -73.9396, 10);

      expect(nearby.length, equals(1));
      expect(nearby.first.locName, equals('Nearby Location'));
    });
  });

  group('Pending Sync Operations', () {
    test('Add and retrieve pending sync item', () async {
      final pending = PendingSyncLocation(
        locUuid: const Uuid().v4(),
        locName: 'Pending Location',
        lat: 42.8142,
        lon: -73.9396,
        locType: 'factory',
        photos: [],
        createdAt: DateTime.now().toIso8601String(),
        syncAttempts: 0,
      );

      await dbService.addPendingSync(pending);

      final allPending = await dbService.getPendingSync();

      expect(allPending.length, equals(1));
      expect(allPending.first.locName, equals('Pending Location'));
    });

    test('Get pending sync count', () async {
      for (int i = 0; i < 3; i++) {
        await dbService.addPendingSync(PendingSyncLocation(
          locUuid: const Uuid().v4(),
          locName: 'Pending $i',
          lat: 42.0,
          lon: -73.0,
          locType: 'factory',
          createdAt: DateTime.now().toIso8601String(),
        ));
      }

      final count = await dbService.getPendingSyncCount();

      expect(count, equals(3));
    });

    test('Remove pending sync after successful sync', () async {
      final uuid = const Uuid().v4();

      await dbService.addPendingSync(PendingSyncLocation(
        locUuid: uuid,
        locName: 'Pending Location',
        lat: 42.0,
        lon: -73.0,
        locType: 'factory',
        createdAt: DateTime.now().toIso8601String(),
      ));

      expect(await dbService.getPendingSyncCount(), equals(1));

      await dbService.removePendingSync(uuid);

      expect(await dbService.getPendingSyncCount(), equals(0));
    });

    test('Increment sync attempts on failure', () async {
      final uuid = const Uuid().v4();

      await dbService.addPendingSync(PendingSyncLocation(
        locUuid: uuid,
        locName: 'Failing Location',
        lat: 42.0,
        lon: -73.0,
        locType: 'factory',
        createdAt: DateTime.now().toIso8601String(),
        syncAttempts: 0,
      ));

      await dbService.incrementSyncAttempts(uuid);

      final pending = await dbService.getPendingSync();

      expect(pending.first.syncAttempts, equals(1));
    });
  });

  group('Sync Log Operations', () {
    test('Add and retrieve sync log entries', () async {
      final entry = SyncLogEntry(
        syncId: const Uuid().v4(),
        syncType: 'bidirectional',
        timestamp: DateTime.now().toIso8601String(),
        itemsSynced: 5,
        conflicts: 0,
        status: 'success',
      );

      await dbService.addSyncLog(entry);

      final logs = await dbService.getSyncLogs(limit: 10);

      expect(logs.length, equals(1));
      expect(logs.first.itemsSynced, equals(5));
      expect(logs.first.status, equals('success'));
    });

    test('Get last successful sync time', () async {
      final now = DateTime.now();

      await dbService.addSyncLog(SyncLogEntry(
        syncId: const Uuid().v4(),
        syncType: 'bidirectional',
        timestamp: now.toIso8601String(),
        itemsSynced: 5,
        conflicts: 0,
        status: 'success',
      ));

      final lastSync = await dbService.getLastSyncTime();

      expect(lastSync, isNotNull);
      expect(lastSync!.year, equals(now.year));
      expect(lastSync.month, equals(now.month));
    });
  });

  group('Database Statistics', () {
    test('Get accurate database stats', () async {
      // Add 2 locations
      for (int i = 0; i < 2; i++) {
        await dbService.upsertLocation(Location(
          locUuid: const Uuid().v4(),
          locName: 'Location $i',
          lat: 42.0,
          lon: -73.0,
          locType: 'factory',
        ));
      }

      // Add 3 pending sync items
      for (int i = 0; i < 3; i++) {
        await dbService.addPendingSync(PendingSyncLocation(
          locUuid: const Uuid().v4(),
          locName: 'Pending $i',
          lat: 42.0,
          lon: -73.0,
          locType: 'factory',
          createdAt: DateTime.now().toIso8601String(),
        ));
      }

      final stats = await dbService.getStats();

      expect(stats['locations'], equals(2));
      expect(stats['pending_sync'], equals(3));
    });
  });
}
