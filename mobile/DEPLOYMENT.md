# AUPAT Mobile App - Deployment Guide

Complete guide for building and deploying the Flutter mobile app.

## Prerequisites

### Required Tools
- Flutter SDK 3.16+ (https://flutter.dev/docs/get-started/install)
- Dart 3.2+
- Android Studio (for Android builds)
- Xcode 15+ (for iOS builds, Mac only)
- CocoaPods (for iOS dependencies)

### Backend Requirements
- AUPAT Core API running and accessible
- Network connectivity between mobile device and AUPAT server

## Setup Instructions

### 1. Install Flutter Dependencies

```bash
cd /home/user/aupat/mobile
flutter pub get
```

This will download all dependencies defined in `pubspec.yaml`.

### 2. Generate JSON Serialization Code

```bash
flutter pub run build_runner build --delete-conflicting-outputs
```

This generates `location_model.g.dart` and other serialization files.

### 3. Configure API Endpoint

Before building, you can set the default API URL in the app. Edit `lib/api/aupat_api_client.dart`:

```dart
static const String _defaultBaseUrl = 'http://YOUR_DESKTOP_IP:5002';
```

Or configure it later in the app settings.

## Building the App

### Android Build

#### Debug APK (for testing)
```bash
flutter build apk --debug
```

Output: `build/app/outputs/flutter-apk/app-debug.apk`

#### Release APK (for distribution)
```bash
flutter build apk --release
```

Output: `build/app/outputs/flutter-apk/app-release.apk`

#### App Bundle (for Google Play Store)
```bash
flutter build appbundle --release
```

Output: `build/app/outputs/bundle/release/app-release.aab`

### iOS Build (Mac only)

#### Debug Build
```bash
flutter build ios --debug
```

#### Release Build
```bash
flutter build ios --release
```

Then open `ios/Runner.xcworkspace` in Xcode and archive the app.

## Installation

### Android Installation

#### Via ADB (USB debugging)
```bash
adb install build/app/outputs/flutter-apk/app-release.apk
```

#### Via File Transfer
1. Transfer APK to Android device
2. Enable "Install from unknown sources" in Android settings
3. Tap the APK file to install

### iOS Installation

#### TestFlight (Recommended)
1. Upload `.ipa` to App Store Connect
2. Add beta testers
3. Install via TestFlight app

#### Direct Installation (Development)
1. Connect iOS device to Mac
2. Open project in Xcode
3. Select device and click Run

## Configuration

### First Run Setup

1. **Launch the app**
2. **Navigate to Settings tab**
3. **Configure API URL**:
   - Local network: `http://192.168.1.X:5002` (replace X with desktop IP)
   - Cloudflare tunnel: `https://aupat.yourdomain.com`
4. **Test Connection** to verify API is reachable
5. **Grant Permissions**:
   - Location (required for GPS capture)
   - Camera (for photo capture)
   - Storage (for photo access)

### Finding Desktop IP Address

On desktop (Linux/Mac):
```bash
ip addr show | grep inet
# or
ifconfig | grep inet
```

On desktop (Docker container):
```bash
docker exec aupat-core hostname -I
```

The mobile app must be on the same WiFi network as the desktop, or use Cloudflare tunnel for remote access.

## Offline Maps Setup

For offline map functionality, you need to generate MBTiles for your region.

### Generate MBTiles

Use one of these tools:
- **TileMill**: https://tilemill-project.github.io/tilemill/
- **QGIS**: Export map tiles as MBTiles
- **mbutil**: Convert tile pyramid to MBTiles

### Add MBTiles to App

1. Place `.mbtiles` file in `assets/map_tiles/`
2. Update `pubspec.yaml` to include the file
3. Modify `lib/screens/map_screen.dart` to use MBTiles provider:

```dart
TileLayer(
  tileProvider: MBTilesTileProvider(
    mbtiles: MBTilesStore.fromPath('/path/to/tiles.mbtiles'),
  ),
  maxZoom: 18,
)
```

## Testing

### Run Unit Tests
```bash
flutter test
```

### Run Widget Tests
```bash
flutter test test/widgets/
```

### Run Integration Tests (requires device/emulator)
```bash
flutter drive --target=test_driver/app.dart
```

## Troubleshooting

### Common Issues

**1. API Connection Fails**
- Verify desktop IP address is correct
- Check firewall allows port 5002
- Ensure mobile device is on same WiFi network
- Test with `curl http://DESKTOP_IP:5002/api/health` from mobile browser

**2. GPS Not Working**
- Grant location permissions in device settings
- Enable location services on device
- Test outdoors for better GPS signal

**3. Build Errors**
- Run `flutter clean && flutter pub get`
- Check Flutter SDK version: `flutter doctor`
- Ensure all dependencies are compatible

**4. Sync Fails**
- Check pending sync count in settings
- Verify WiFi connection (sync only on WiFi)
- Review sync logs in settings

### Logs and Debugging

**View Flutter logs:**
```bash
flutter logs
```

**Android device logs:**
```bash
adb logcat | grep flutter
```

**iOS device logs:**
```bash
idevicesyslog | grep flutter
```

## Performance Optimization

### Release Build Optimizations

Flutter automatically applies these in release builds:
- Tree-shaking (removes unused code)
- Minification (reduces code size)
- Obfuscation (protects code)

### Database Performance

For large datasets (1000+ locations):
- Ensure indexes are created (handled by DatabaseService)
- Use pagination for location lists
- Implement virtual scrolling for long lists

### Memory Management

- Dispose controllers in `dispose()` methods
- Close database connections when not needed
- Clear image caches periodically

## Updating the App

### Version Updates

1. Update version in `pubspec.yaml`:
   ```yaml
   version: 0.1.3+2  # Format: version+buildNumber
   ```

2. Rebuild the app:
   ```bash
   flutter build apk --release
   ```

3. Distribute updated APK/AAB

### Database Migrations

Database migrations are handled automatically by `DatabaseService`:
- Version checks on app startup
- Alembic-style migrations
- Backward compatibility maintained

## Security Considerations

### API Security

- Use HTTPS for production (Cloudflare tunnel)
- Consider API key authentication (future)
- Validate all user inputs
- Sanitize database queries

### Data Privacy

- GPS data stored locally until sync
- Photos stored on device until WiFi sync
- No data sent without user action
- Can clear all data in settings

### App Permissions

Required permissions (Android):
- `ACCESS_FINE_LOCATION` - GPS capture
- `CAMERA` - Photo capture
- `READ_EXTERNAL_STORAGE` - Photo access

Required permissions (iOS):
- `NSLocationWhenInUseUsageDescription` - GPS capture
- `NSCameraUsageDescription` - Photo capture
- `NSPhotoLibraryUsageDescription` - Photo access

## Production Deployment Checklist

- [ ] Update version number in pubspec.yaml
- [ ] Configure production API URL
- [ ] Test on multiple devices (Android + iOS)
- [ ] Run full test suite
- [ ] Build release APK/AAB
- [ ] Sign app with production keys
- [ ] Test installation on clean device
- [ ] Verify GPS capture works
- [ ] Verify sync to desktop works
- [ ] Review permissions and privacy policy
- [ ] Upload to distribution platform (Play Store, TestFlight, etc.)

## Support

For issues or questions:
- GitHub Issues: https://github.com/bizzlechizzle/aupat/issues
- Documentation: /docs/v0.1.2/
- API Reference: http://YOUR_API:5002/
