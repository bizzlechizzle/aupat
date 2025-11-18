# Self-Signed Certificate Workflow for macOS

Guide for creating and using self-signed certificates to run Abandoned Upstate on macOS without a paid Apple Developer account.

## Overview

This workflow is suitable for:
- Personal use on your own Mac
- Testing and development
- Local deployment without distribution

**Limitations:**
- Only works on the Mac where certificate is created
- Requires manual trust configuration
- Cannot be distributed to other users
- Auto-updates will not work reliably
- Gatekeeper warnings may still appear

**For production distribution**, consider purchasing an Apple Developer account ($99/year).

---

## Prerequisites

- macOS 10.13 or later
- Xcode Command Line Tools installed
- Administrator access to your Mac
- Keychain Access app (built into macOS)

---

## Step 1: Create Self-Signed Certificate

### Using Keychain Access (GUI Method)

1. Open **Keychain Access** (Applications → Utilities → Keychain Access)

2. From the menu: **Keychain Access → Certificate Assistant → Create a Certificate**

3. Configure the certificate:
   - **Name:** `Abandoned Upstate Developer`
   - **Identity Type:** Self Signed Root
   - **Certificate Type:** Code Signing
   - **Let me override defaults:** Check this box
   - Click **Continue**

4. Certificate Information:
   - **Serial Number:** (leave default)
   - **Validity Period (days):** 3650 (10 years)
   - Click **Continue**

5. Email and Name:
   - **Email:** your@email.com (optional)
   - **Name:** Your Name
   - Click **Continue**

6. Key Pair Information:
   - **Algorithm:** RSA
   - **Key Size:** 2048 bits
   - Click **Continue** through remaining screens

7. Keychain:
   - **Keychain:** login
   - Click **Create**

8. Enter your Mac password when prompted

### Using Command Line (Alternative)

```bash
# Generate certificate
security create-keychain -p "" build.keychain
security default-keychain -s build.keychain
security unlock-keychain -p "" build.keychain

security add-certificates -k build.keychain

# Create certificate
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 3650 -nodes \
  -subj "/CN=Abandoned Upstate Developer/O=Self Signed/C=US"

# Import to keychain
security import cert.pem -k ~/Library/Keychains/login.keychain-db
security import key.pem -k ~/Library/Keychains/login.keychain-db
```

---

## Step 2: Trust the Certificate

### Make Certificate Trusted

1. In **Keychain Access**, select **login** keychain (left sidebar)

2. Find your certificate: `Abandoned Upstate Developer`

3. Double-click the certificate to open details

4. Expand **Trust** section

5. Set **Code Signing** to **Always Trust**

6. Close the window (enter password when prompted)

7. Verify: The certificate should now show a blue plus sign indicating it's trusted

---

## Step 3: Configure electron-builder

### Update package.json

Add or update the `build.mac` section in `desktop/package.json`:

```json
{
  "build": {
    "mac": {
      "category": "public.app-category.lifestyle",
      "icon": "resources/icon.icns",
      "target": ["dmg", "zip"],
      "identity": "Abandoned Upstate Developer",
      "hardenedRuntime": false,
      "gatekeeperAssess": false,
      "type": "distribution"
    }
  }
}
```

**Key settings:**
- `identity`: Matches certificate name exactly
- `hardenedRuntime: false`: Required for self-signed certs
- `gatekeeperAssess: false`: Skip Gatekeeper validation

---

## Step 4: Build Signed App

### Build Process

1. Navigate to desktop directory:
   ```bash
   cd desktop
   ```

2. Ensure dependencies are installed:
   ```bash
   npm install
   ```

3. Build the application:
   ```bash
   npm run package:mac
   ```

4. electron-builder will:
   - Build the app
   - Sign it with your self-signed certificate
   - Create a .dmg installer
   - Create a .zip for auto-updates

### Verify Signing

Check if the app was signed:

```bash
codesign -dv --verbose=4 dist-builder/mac/Abandoned\ Upstate.app
```

Expected output should include:
```
Authority=Abandoned Upstate Developer
```

---

## Step 5: Install and Run

### Install the App

1. Open the .dmg file:
   ```bash
   open dist-builder/Abandoned\ Upstate-*.dmg
   ```

2. Drag **Abandoned Upstate** to **Applications** folder

3. Eject the disk image

### First Launch

**Option 1: Right-click method**
1. Navigate to Applications folder
2. Right-click **Abandoned Upstate**
3. Click **Open**
4. Click **Open** again in the security dialog

**Option 2: Command line**
```bash
# Remove quarantine attribute
xattr -cr /Applications/Abandoned\ Upstate.app

# Launch the app
open -a "Abandoned Upstate"
```

**Option 3: System Preferences**
1. Try to open the app normally (will fail)
2. Go to **System Preferences → Security & Privacy**
3. Click **Open Anyway** button
4. Click **Open** in the dialog

---

## Troubleshooting

### Certificate Not Found

**Error:** `No identity found for signing`

**Cause:** Certificate name doesn't match or not in keychain

**Fix:**
1. Open Keychain Access
2. Find your certificate
3. Copy the exact name
4. Update `identity` in package.json to match exactly

### Certificate Not Trusted

**Error:** App won't open, says "damaged"

**Fix:**
```bash
# Trust the certificate in keychain
security find-identity -v -p codesigning

# Look for your certificate in the list
# If it has "(invalid)" next to it, mark it as trusted in Keychain Access
```

### Gatekeeper Still Blocking

**Error:** "Cannot be opened because the developer cannot be verified"

**Fix:**
```bash
# Remove quarantine attribute
sudo xattr -rd com.apple.quarantine /Applications/Abandoned\ Upstate.app
```

### Build Fails with Signing Error

**Error:** `Command failed: codesign --sign...`

**Fix:**
```bash
# Skip signing temporarily to test
CSC_IDENTITY_AUTO_DISCOVERY=false npm run package:mac

# Or specify identity explicitly
export CSC_NAME="Abandoned Upstate Developer"
npm run package:mac
```

### Auto-Updates Not Working

**Expected:** Self-signed apps cannot reliably auto-update

**Reason:** macOS Gatekeeper blocks downloaded updates that aren't notarized

**Workaround:** Manual updates only
1. Download new .dmg from GitHub releases
2. Replace app in Applications folder
3. Use right-click → Open method again

---

## Limitations and Workarounds

### Cannot Distribute to Others

**Limitation:** Self-signed certificate only works on your Mac

**Workaround:** Recipients must:
1. Create their own self-signed certificate
2. Re-sign the app themselves: `codesign -f -s "Their Cert Name" Abandoned\ Upstate.app`

### Cannot Notarize

**Limitation:** Only Apple Developer Program members can notarize

**Impact:** Gatekeeper warnings on macOS 10.15+

**Workaround:** Use right-click → Open method

### Auto-Update Security Warnings

**Limitation:** Updated versions trigger Gatekeeper again

**Workaround:**
- Disable auto-update (already done in development mode)
- Manual updates with right-click → Open each time

---

## Upgrading to Official Signing

When ready to purchase Apple Developer account:

### Prerequisites

1. Enroll in [Apple Developer Program](https://developer.apple.com/programs/) ($99/year)

2. Wait for approval (usually 24-48 hours)

3. Generate certificates in Apple Developer Portal

### Update Configuration

Update `desktop/package.json`:

```json
{
  "build": {
    "mac": {
      "identity": "Developer ID Application: Your Name (TEAM_ID)",
      "hardenedRuntime": true,
      "gatekeeperAssess": false,
      "entitlements": "build/entitlements.mac.plist",
      "entitlementsInherit": "build/entitlements.mac.plist"
    }
  }
}
```

### Create Entitlements File

Create `desktop/build/entitlements.mac.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
  <true/>
  <key>com.apple.security.cs.allow-jit</key>
  <true/>
</dict>
</plist>
```

### Notarization

After building with official certificate:

```bash
# Submit for notarization
xcrun notarytool submit dist-builder/*.dmg \
  --apple-id your@email.com \
  --team-id TEAM_ID \
  --password app-specific-password \
  --wait

# Staple notarization ticket
xcrun stapler staple dist-builder/*.dmg
```

---

## Security Considerations

### Self-Signed Certificates

**Pros:**
- Free
- No waiting for Apple approval
- Full control
- Good for personal use

**Cons:**
- No trust chain validation
- Cannot distribute
- Gatekeeper warnings persist
- No notarization support

### Best Practices

1. **Use strong passwords** for keychain
2. **Backup certificate** to secure location
3. **Limit certificate validity** (1-2 years recommended)
4. **Never share** your certificate with others
5. **Rotate certificates** periodically

### Export Certificate Backup

```bash
# Export certificate and private key
security export -k login.keychain -t identities -f pkcs12 \
  -o abandoned-upstate-cert.p12 \
  -P "strong-password"

# Store in secure location (password manager, encrypted drive)
```

### Restore Certificate Backup

```bash
# Import certificate on new Mac
security import abandoned-upstate-cert.p12 \
  -k ~/Library/Keychains/login.keychain-db \
  -P "strong-password"
```

---

## FAQ

**Q: Do I need to recreate the certificate for each build?**
A: No, create once and reuse for all builds until expiration.

**Q: Can I use the same certificate for other apps?**
A: Yes, but create app-specific certificates for better organization.

**Q: Will this work on Apple Silicon (M1/M2)?**
A: Yes, self-signing works on both Intel and Apple Silicon Macs.

**Q: Can I automate this in CI/CD?**
A: Not recommended for self-signed certs. Use official Apple Developer certificates in CI/CD.

**Q: What if my certificate expires?**
A: Create a new certificate and rebuild the app. Old builds may still work if already trusted.

**Q: Is this safe for production use?**
A: For personal use only. For production, purchase Apple Developer account.

---

## Additional Resources

- [Apple Code Signing Guide](https://developer.apple.com/library/archive/documentation/Security/Conceptual/CodeSigningGuide/)
- [electron-builder macOS Signing](https://www.electron.build/code-signing)
- [Keychain Access User Guide](https://support.apple.com/guide/keychain-access/)
- [Gatekeeper Documentation](https://support.apple.com/en-us/HT202491)
