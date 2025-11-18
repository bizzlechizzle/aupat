# AUPAT Mobile App - Production Deployment Guide

Version: 0.1.2
Date: 2025-11-18
Status: Production Ready

## Overview

This document provides complete instructions for building, testing, and deploying the AUPAT mobile app to production environments.

## Prerequisites

### Development Environment

**Required:**
- Flutter SDK 3.16.0 or higher
- Dart SDK 3.2.0 or higher
- Android Studio or VS Code with Flutter extensions
- Java JDK 17 or higher
- Android SDK with API level 33 (Android 13)

**Optional (for iOS):**
- macOS with Xcode 15 or higher
- iOS 14.0 or higher target
- Apple Developer account

**Verify Installation:**
```bash
flutter doctor -v
```

All checkmarks should be green for Android development.

### Backend Requirements

AUPAT Core API must be running and accessible:
- Default: `http://localhost:5002`
- Or configured custom endpoint
- Backend must have mobile sync endpoints enabled

## Build Process

### Option 1: Automated Build Script

```bash
cd mobile

# Full production build with tests
./build.sh --clean --test --release

# Quick build without tests
./build.sh --release

# Debug build for testing
./build.sh --debug
```

The script will:
1. Verify Flutter installation
2. Clean build artifacts (if --clean)
3. Install dependencies
4. Run code generation
5. Run tests (if --test)
6. Analyze code
7. Build APK

Output: `build/app/outputs/flutter-apk/app-release.apk`

### Option 2: Manual Build

```bash
cd mobile

# Install dependencies
flutter pub get

# Run code generation
flutter pub run build_runner build --delete-conflicting-outputs

# Run tests
flutter test

# Analyze code
flutter analyze

# Build release APK
flutter build apk --release

# Output: build/app/outputs/flutter-apk/app-release.apk
```

### Build Variants

**Release APK (recommended):**
```bash
flutter build apk --release
```
- Optimized and minified
- No debugging symbols
- ~15-25 MB
- Suitable for distribution

**Debug APK (development):**
```bash
flutter build apk --debug
```
- Includes debugging symbols
- Larger file size (~40-60 MB)
- Hot reload enabled
- Not for production

**App Bundle (Google Play):**
```bash
flutter build appbundle --release
```
- Optimized for Play Store
- Dynamic delivery enabled
- Smaller download size
- Recommended for Play Store uploads

## Code Signing (Android)

### Generate Signing Key (First Time Only)

```bash
cd mobile/android

keytool -genkey -v \
  -keystore aupat-release-key.jks \
  -keyalg RSA \
  -keysize 2048 \
  -validity 10000 \
  -alias aupat-key
```

**Important:**
- Store keystore password securely
- Backup `aupat-release-key.jks` file
- Never commit keystore to git

### Configure Signing

Create `mobile/android/key.properties`:

```properties
storePassword=YOUR_KEYSTORE_PASSWORD
keyPassword=YOUR_KEY_PASSWORD
keyAlias=aupat-key
storeFile=/path/to/aupat-release-key.jks
```

Add to `.gitignore`:
```
android/key.properties
android/*.jks
```

Update `mobile/android/app/build.gradle`:

```gradle
def keystoreProperties = new Properties()
def keystorePropertiesFile = rootProject.file('key.properties')
if (keystorePropertiesFile.exists()) {
    keystoreProperties.load(new FileInputStream(keystorePropertiesFile))
}

android {
    ...
    signingConfigs {
        release {
            keyAlias keystoreProperties['keyAlias']
            keyPassword keystoreProperties['keyPassword']
            storeFile keystoreProperties['storeFile'] ? file(keystoreProperties['storeFile']) : null
            storePassword keystoreProperties['storePassword']
        }
    }
    buildTypes {
        release {
            signingConfig signingConfigs.release
        }
    }
}
```

## Testing Before Deployment

### 1. Unit Tests

```bash
cd mobile
flutter test

# With coverage
flutter test --coverage
```

Expected: All tests pass

### 2. Integration Tests

```bash
flutter test integration_test/
```

### 3. Device Testing

```bash
# List connected devices
adb devices

# Install on device
adb install build/app/outputs/flutter-apk/app-release.apk

# View logs
adb logcat -s flutter
```

**Test Checklist:**
- [ ] App launches successfully
- [ ] GPS capture works with <10m accuracy
- [ ] Camera capture works
- [ ] Gallery import works
- [ ] Photos display in grid
- [ ] Location save works
- [ ] WiFi sync works with backend
- [ ] Offline mode works
- [ ] App doesn't crash on common workflows
- [ ] Permissions requested correctly

### 4. Backend Integration Testing

```bash
# Start AUPAT Core API
cd /path/to/aupat
python app.py

# Configure mobile app to point to backend
# Settings > API URL: http://YOUR_IP:5002

# Test sync workflow:
# 1. Create location with photos on mobile
# 2. Connect to WiFi
# 3. Trigger sync
# 4. Verify location appears in desktop app
# 5. Verify photos saved to /app/data/mobile_photos/
```

## Deployment Checklist

### Pre-Deployment

- [ ] All tests passing (unit + integration)
- [ ] Code analysis clean (`flutter analyze`)
- [ ] Version bumped in `pubspec.yaml`
- [ ] Changelog updated
- [ ] Backend API endpoints verified working
- [ ] Signing key configured (for release builds)
- [ ] Documentation updated

### Build Verification

- [ ] APK builds without errors
- [ ] APK size reasonable (<30 MB for release)
- [ ] SHA256 hash calculated and recorded
- [ ] APK tested on physical device
- [ ] No crashes during basic workflows
- [ ] Sync functionality verified

### Distribution

**Internal Testing:**
```bash
# Share APK via email or file share
# Install with: adb install app-release.apk
```

**Google Play Store (Future):**
1. Create Google Play Developer account
2. Create app listing
3. Upload app bundle: `flutter build appbundle --release`
4. Configure store listing (screenshots, description)
5. Submit for review

**Direct Distribution:**
1. Host APK on secure server
2. Provide SHA256 hash for verification
3. Enable "Install from Unknown Sources" on device
4. Download and install APK

## Version Management

Update version in `mobile/pubspec.yaml`:

```yaml
version: 0.1.2+1
#        ^     ^
#        |     |
#        |     Build number (increment for each build)
#        Version name (semantic versioning)
```

**Versioning Strategy:**
- MAJOR: Breaking changes
- MINOR: New features (backwards compatible)
- PATCH: Bug fixes
- BUILD: Internal build number

Example progression:
- 0.1.0+1 - Initial release
- 0.1.1+2 - Bug fix
- 0.1.2+3 - Photo feature added
- 0.2.0+4 - Major new feature
- 1.0.0+5 - Production release

## Troubleshooting

### Build Errors

**Error: Flutter SDK not found**
```bash
# Verify installation
flutter doctor

# Add to PATH
export PATH="$PATH:/path/to/flutter/bin"
```

**Error: Gradle build failed**
```bash
cd mobile/android
./gradlew clean

cd ..
flutter clean
flutter pub get
flutter build apk --release
```

**Error: Out of memory**
```bash
# Increase Gradle memory
echo "org.gradle.jvmargs=-Xmx2048m" >> android/gradle.properties
```

**Error: Signing key not found**
- Verify `key.properties` exists
- Check `storeFile` path is absolute
- Ensure keystore file exists

### Runtime Errors

**Error: GPS not working**
- Check AndroidManifest.xml has location permissions
- Verify GPS enabled on device
- Test outdoors for better signal

**Error: Camera not working**
- Check AndroidManifest.xml has camera permissions
- Verify camera permission granted in app settings
- Test with device camera app first

**Error: Sync fails**
- Verify backend API is running
- Check API URL in app settings
- Ensure device on same network as backend
- Check backend logs for errors

**Error: App crashes on startup**
```bash
# View crash logs
adb logcat -s flutter

# Common causes:
# - Missing permissions in AndroidManifest.xml
# - Database migration issues
# - Network configuration problems
```

## Performance Optimization

### APK Size Reduction

```bash
# Build with code shrinking
flutter build apk --release --shrink

# Build split APKs per ABI
flutter build apk --release --split-per-abi
```

### Database Optimization

SQLite database auto-vacuums and uses WAL mode. No manual optimization needed for typical usage.

### Photo Optimization

Photos compressed to ~200-500KB each. For further optimization:
- Adjust quality in `camera_service.dart` (currently 85%)
- Implement background cleanup of synced photos
- Add storage usage monitoring

## Monitoring and Analytics

### Crash Reporting (Future)

Integrate Sentry or Firebase Crashlytics:

```dart
// main.dart
import 'package:sentry_flutter/sentry_flutter.dart';

Future<void> main() async {
  await SentryFlutter.init(
    (options) {
      options.dsn = 'YOUR_SENTRY_DSN';
    },
    appRunner: () => runApp(MyApp()),
  );
}
```

### Analytics (Future)

Firebase Analytics or custom events:
- Location capture events
- Photo upload metrics
- Sync success/failure rates
- User engagement metrics

## Security Considerations

### API Security

Current: HTTP only (development)
Production: Should use HTTPS

```dart
// Update in settings
apiUrl: 'https://your-domain.com:5002'
```

### Data Privacy

- GPS coordinates stored locally until sync
- Photos stored in app-private directory
- No analytics or tracking by default
- User controls all data

### Permissions

Required permissions (AndroidManifest.xml):
- ACCESS_FINE_LOCATION - GPS capture
- CAMERA - Photo capture
- READ_EXTERNAL_STORAGE - Gallery import (Android <13)
- READ_MEDIA_IMAGES - Gallery import (Android 13+)
- INTERNET - API sync
- ACCESS_WIFI_STATE - WiFi detection

All permissions requested at runtime with user consent.

## Rollback Procedure

If critical issues found in production:

1. **Immediate:** Remove APK from distribution
2. **Notify:** Alert active users via email/notification
3. **Rollback:** Provide previous stable version
4. **Fix:** Address issue in development
5. **Test:** Thorough testing before re-release
6. **Deploy:** New version with fix

## Support and Maintenance

### User Support

Common user issues:
1. GPS not accurate - Wait for better signal, use outdoors
2. Photos not syncing - Check WiFi connection and backend URL
3. App crashes - Clear app data and reinstall

### Backend Maintenance

Mobile sync endpoints require:
- `/api/sync/mobile` - Push endpoint
- `/api/sync/mobile/pull` - Pull endpoint
- Database access to `locations` and `sync_log` tables

Monitor backend logs for:
- Failed sync requests
- Photo processing errors
- Database conflicts

## Continuous Improvement

### Planned Enhancements

1. **Immich Integration** - Auto-upload photos from backend
2. **Offline Photo Viewer** - View captured photos in app
3. **Background Sync** - Periodic automatic sync
4. **Multi-device Support** - Sync across multiple mobile devices
5. **Photo Annotations** - Add notes and tags to photos

### Feedback Collection

Gather user feedback on:
- GPS accuracy issues
- Photo quality preferences
- Sync reliability
- UI/UX improvements

## Appendix

### File Structure

```
mobile/
├── android/              # Android platform code
├── ios/                  # iOS platform code
├── lib/                  # Dart source code
│   ├── main.dart        # Entry point
│   ├── models/          # Data models
│   ├── screens/         # UI screens
│   ├── services/        # Business logic
│   └── api/             # API client
├── test/                # Unit tests
├── pubspec.yaml         # Dependencies
├── build.sh             # Build script
└── README.md            # Documentation
```

### Useful Commands

```bash
# Check Flutter version
flutter --version

# List devices
flutter devices

# Run app in debug mode
flutter run

# Hot reload (during flutter run)
# Press 'r' in terminal

# Hot restart
# Press 'R' in terminal

# View logs
flutter logs

# Clean build
flutter clean

# Update dependencies
flutter pub upgrade
```

### Resources

- Flutter Documentation: https://flutter.dev/docs
- Dart Documentation: https://dart.dev/guides
- Android Studio: https://developer.android.com/studio
- AUPAT Project: https://github.com/bizzlechizzle/aupat

---

**Document Version:** 1.0
**Last Updated:** 2025-11-18
**Maintainer:** AUPAT Development Team
