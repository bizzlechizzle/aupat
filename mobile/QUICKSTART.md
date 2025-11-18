# AUPAT Mobile - Quick Start Guide

Get the mobile app running in under 10 minutes.

## Prerequisites Check

Before starting, verify you have:
- [ ] Flutter SDK 3.16+ installed (`flutter --version`)
- [ ] AUPAT backend running (desktop or Docker)
- [ ] Android Studio (for Android) or Xcode (for iOS)

## Step 1: Install Dependencies

```bash
cd /home/user/aupat/mobile
flutter pub get
```

This installs all required packages from `pubspec.yaml`.

## Step 2: Generate Code

```bash
flutter pub run build_runner build --delete-conflicting-outputs
```

This generates `location_model.g.dart` for JSON serialization.

## Step 3: Find Your Desktop API URL

### Option A: Local Network (Recommended for Development)

Find your desktop's IP address:

**On Linux/Mac:**
```bash
hostname -I | awk '{print $1}'
# Example output: 192.168.1.100
```

**On Windows:**
```bash
ipconfig | findstr IPv4
# Example output: 192.168.1.100
```

Your API URL will be: `http://192.168.1.100:5002`

### Option B: Cloudflare Tunnel (For Remote Access)

If you've set up Cloudflare tunnel: `https://aupat.yourdomain.com`

### Option C: Localhost (Emulator Only)

- **Android Emulator:** `http://10.0.2.2:5002`
- **iOS Simulator:** `http://localhost:5002`

## Step 4: Build the App

### For Android

**Debug Build (Fast, for testing):**
```bash
flutter build apk --debug
```
Output: `build/app/outputs/flutter-apk/app-debug.apk`

**Release Build (Optimized):**
```bash
flutter build apk --release
```
Output: `build/app/outputs/flutter-apk/app-release.apk`

### For iOS (Mac Only)

**Debug Build:**
```bash
flutter build ios --debug
```

**Release Build:**
```bash
flutter build ios --release
# Then open ios/Runner.xcworkspace in Xcode
```

## Step 5: Install on Device

### Android via USB

1. Enable USB debugging on Android device:
   - Settings → About Phone → Tap "Build Number" 7 times
   - Settings → Developer Options → Enable "USB Debugging"

2. Connect device via USB

3. Verify device is connected:
   ```bash
   flutter devices
   ```

4. Install app:
   ```bash
   flutter install
   # or
   adb install build/app/outputs/flutter-apk/app-release.apk
   ```

### Android via File Transfer

1. Transfer APK to phone (email, USB, cloud storage)
2. On phone: Settings → Security → Enable "Install from Unknown Sources"
3. Tap the APK file to install

### iOS via Xcode

1. Open `ios/Runner.xcworkspace` in Xcode
2. Connect iPhone via USB
3. Select your device in Xcode
4. Click Run (▶️) button

## Step 6: First Launch Configuration

1. **Launch AUPAT Mobile** on your device

2. **Navigate to Settings tab** (bottom navigation, gear icon)

3. **Configure API URL:**
   - Tap "API Base URL" field
   - Enter your desktop's URL (e.g., `http://192.168.1.100:5002`)
   - Tap "Save"

4. **Test Connection:**
   - Tap "Test" button
   - Should see "Connection Successful" with response time
   - If failed, verify:
     - Desktop API is running (`curl http://YOUR_IP:5002/api/health`)
     - Phone is on same WiFi network as desktop
     - Firewall allows port 5002

5. **Grant Permissions:**
   - When prompted, allow Location access (for GPS capture)
   - When prompted, allow Camera access (for future photo feature)

## Step 7: Test Core Features

### Test 1: GPS Capture

1. Go to **Add tab** (bottom navigation, + icon)
2. Enter location name: "Test Location"
3. Select type: "Factory"
4. Tap **"Capture GPS"** button
5. Wait for GPS lock (should take <10 seconds outdoors)
6. Verify accuracy is <10 meters (green text)
7. Tap **"Save Location"**
8. Should see success message: "Location saved! Will sync when on WiFi."

### Test 2: View Locations

1. Go to **Locations tab** (bottom navigation, list icon)
2. Should see "Test Location" in the list
3. Tap the location to view details
4. Verify GPS coordinates are shown

### Test 3: Map View

1. Go to **Map tab** (bottom navigation, map icon)
2. Should see map with location marker
3. Tap marker to see location details in bottom sheet
4. Tap "My Location" floating button (bottom right)
5. Map should center on your current GPS position

### Test 4: Manual Sync

1. Ensure WiFi is connected
2. Go to **Settings tab**
3. Tap **"Manual Sync"** button
4. Should see "Sync successful" message
5. Check "Pending: 0 items" (should decrease after sync)

### Test 5: Verify on Desktop

1. On desktop, check AUPAT database:
   ```bash
   sqlite3 /home/user/aupat/data/aupat.db
   SELECT loc_name, lat, lon FROM locations ORDER BY json_update DESC LIMIT 5;
   ```

2. Should see "Test Location" with GPS coordinates from mobile

## Troubleshooting

### API Connection Fails

**Problem:** "Connection Failed" when testing API

**Solutions:**
1. Verify backend is running:
   ```bash
   curl http://localhost:5002/api/health
   # Should return: {"status":"ok","version":"0.1.2",...}
   ```

2. Check Docker container (if using Docker):
   ```bash
   docker ps | grep aupat-core
   docker logs aupat-core
   ```

3. Verify firewall allows port 5002:
   ```bash
   # Linux
   sudo ufw allow 5002

   # Mac
   # System Preferences → Security & Privacy → Firewall → Options
   ```

4. Try desktop IP from phone browser:
   - Open Safari/Chrome on phone
   - Navigate to `http://YOUR_DESKTOP_IP:5002`
   - Should see AUPAT API info page

### GPS Not Working

**Problem:** GPS capture fails or shows "Permission denied"

**Solutions:**
1. Grant location permission:
   - Android: Settings → Apps → AUPAT → Permissions → Location → Allow
   - iOS: Settings → Privacy → Location Services → AUPAT → While Using App

2. Enable location services:
   - Android: Settings → Location → On
   - iOS: Settings → Privacy → Location Services → On

3. Test outdoors (GPS doesn't work well indoors)

4. Wait longer (first GPS lock can take 30-60 seconds)

### Sync Doesn't Happen Automatically

**Problem:** Locations stay in pending sync even on WiFi

**Solutions:**
1. Background sync restrictions:
   - Android: Settings → Apps → AUPAT → Battery → Unrestricted
   - iOS: Background App Refresh must be enabled

2. Use manual sync:
   - Settings tab → "Manual Sync" button
   - Works immediately, doesn't wait for background task

3. Check sync logs:
   - Settings tab → View "Recent Syncs"
   - Shows sync status and errors

### Build Errors

**Problem:** `flutter build apk` fails

**Solutions:**
1. Clean and rebuild:
   ```bash
   flutter clean
   flutter pub get
   flutter build apk
   ```

2. Check Flutter doctor:
   ```bash
   flutter doctor -v
   # Fix any issues reported
   ```

3. Update Flutter:
   ```bash
   flutter upgrade
   ```

## Performance Tips

### For Best GPS Accuracy
- Use outdoors with clear sky view
- Wait for "green" accuracy (<10m)
- Avoid tall buildings or dense forests
- First GPS lock takes longer (be patient)

### For Fast Sync
- Ensure strong WiFi signal
- Sync smaller batches (<50 locations at a time)
- Use manual sync for immediate results
- Check pending count in settings

### For Battery Life
- Disable background sync if not needed (manual sync only)
- Close app when not in use
- Use airplane mode when not syncing
- Enable battery saver on device

## Next Steps

After successful setup:

1. **Create Real Locations:** Go explore and capture abandoned places!

2. **Customize Settings:**
   - Adjust map default center/zoom
   - Configure sync frequency (future)
   - Set up offline map tiles

3. **Sync Regularly:**
   - Manual sync after each field session
   - Or wait for automatic WiFi sync

4. **View on Desktop:**
   - All mobile locations appear on desktop map
   - Edit/enhance on desktop with full features

5. **Read Full Docs:**
   - `DEPLOYMENT.md` - Complete deployment guide
   - `README.md` - Architecture and design
   - `IMPLEMENTATION_SUMMARY.md` - Technical details

## Support

**Logs and Debugging:**
```bash
# View Flutter logs
flutter logs

# View Android device logs
adb logcat | grep flutter

# View iOS device logs (Mac)
idevicesyslog | grep flutter
```

**Common Log Files:**
- Mobile: Check Flutter DevTools
- Backend: `/home/user/aupat/logs/`
- Database: `/home/user/aupat/data/aupat.db`

**Get Help:**
- GitHub Issues: https://github.com/bizzlechizzle/aupat/issues
- Check documentation in `/docs/v0.1.2/`
- Review backend API at: http://YOUR_API:5002/

## Success Checklist

- [ ] Flutter dependencies installed
- [ ] Code generated successfully
- [ ] App built (APK or IPA)
- [ ] Installed on device
- [ ] API URL configured
- [ ] Connection test passed
- [ ] GPS permissions granted
- [ ] Test location created
- [ ] Location appears in list
- [ ] Location visible on map
- [ ] Manual sync successful
- [ ] Location appears on desktop

If all checkboxes are checked: **You're ready to use AUPAT Mobile in the field!**

Time to first working app: **~10 minutes** ✓
