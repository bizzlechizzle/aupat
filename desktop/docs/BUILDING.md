# Building Abandoned Upstate Desktop App

Comprehensive guide for building, packaging, and distributing the Abandoned Upstate desktop application.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Development Build](#development-build)
- [Production Build](#production-build)
- [Platform-Specific Instructions](#platform-specific-instructions)
- [Code Signing](#code-signing)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

- Node.js 20+ LTS
- npm 10+
- Git
- Python 3.9+ (for backend)

### Platform-Specific Requirements

**macOS:**
- Xcode Command Line Tools: `xcode-select --install`
- For distribution: Apple Developer account ($99/year) or self-signed certificate

**Linux:**
- Build tools: `sudo apt-get install build-essential`
- For AppImage: `libfuse2` or `libfuse3`

**Windows:**
- Windows SDK
- Visual Studio Build Tools

---

## Development Build

### Initial Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/bizzlechizzle/aupat.git
   cd aupat
   ```

2. Install dependencies:
   ```bash
   cd desktop
   npm install
   ```

3. Verify installation:
   ```bash
   npm run test
   ```

### Running Development Server

Start the Electron app in development mode:

```bash
npm run dev
```

This command:
- Starts Vite development server with hot-reload
- Launches Electron in development mode
- Enables Chrome DevTools
- Auto-updater is DISABLED in dev mode

### Development Mode vs Production

| Feature | Development | Production |
|---------|-------------|-----------|
| Hot Reload | Yes | No |
| DevTools | Enabled | Disabled |
| Auto-updater | Disabled | Enabled |
| Source Maps | Full | None |
| Minification | No | Yes |

---

## Production Build

### Build Process

1. Ensure you're on the correct branch:
   ```bash
   git checkout main
   git pull origin main
   ```

2. Install/update dependencies:
   ```bash
   npm install
   ```

3. Build the application:
   ```bash
   npm run build
   ```

4. Package for your platform:
   ```bash
   # macOS only
   npm run package:mac

   # Linux only
   npm run package:linux

   # Both platforms
   npm run package
   ```

### Build Artifacts

Packaged builds are output to `desktop/dist-builder/`:

**macOS:**
- `Abandoned Upstate-{version}.dmg` - Installer image
- `Abandoned Upstate-{version}-mac.zip` - Zip archive for auto-updates
- `Abandoned Upstate-{version}-arm64.dmg` - Apple Silicon specific (if built on M1/M2)

**Linux:**
- `Abandoned Upstate-{version}.AppImage` - Portable executable
- `abandoned-upstate_{version}_amd64.deb` - Debian package

### Version Bumping

Update version in `package.json` before building:

```json
{
  "version": "0.2.1"
}
```

Version format: MAJOR.MINOR.PATCH (semantic versioning)

---

## Platform-Specific Instructions

### macOS Build

#### Requirements
- macOS 10.13 or later
- Xcode Command Line Tools
- At least 5 GB free disk space

#### Build Steps

1. Generate app icons (if not done):
   ```bash
   cd desktop
   ./generate-icons.sh
   ```

2. Build and package:
   ```bash
   npm run package:mac
   ```

3. Locate the `.dmg` file in `dist-builder/`

#### Testing the Build

```bash
# Open the DMG
open dist-builder/Abandoned\ Upstate-*.dmg

# Drag app to Applications
# Launch from Applications folder
```

### Linux Build

#### Requirements
- Ubuntu 20.04+ or equivalent
- Build tools installed
- At least 3 GB free disk space

#### Build Steps

1. Install dependencies:
   ```bash
   sudo apt-get update
   sudo apt-get install build-essential libfuse2
   ```

2. Generate icons:
   ```bash
   cd desktop
   ./generate-icons.sh
   ```

3. Build and package:
   ```bash
   npm run package:linux
   ```

4. Locate the `.AppImage` file in `dist-builder/`

#### Testing the Build

```bash
# Make AppImage executable
chmod +x dist-builder/Abandoned\ Upstate-*.AppImage

# Run it
./dist-builder/Abandoned\ Upstate-*.AppImage
```

---

## Code Signing

### Why Code Signing Matters

- macOS Gatekeeper requires signed apps
- Prevents "unidentified developer" warnings
- Enables auto-updates
- Required for App Store distribution

### Options

1. **Paid Apple Developer Account** ($99/year)
   - Official code signing
   - Notarization support
   - No warnings for end users
   - See [Apple Developer Program](https://developer.apple.com/programs/)

2. **Self-Signed Certificate** (Free, local use only)
   - Works on your own Mac
   - Requires manual trust configuration
   - Not suitable for distribution
   - See [docs/SELF_SIGNING.md](./SELF_SIGNING.md)

3. **No Signing** (Development only)
   - Users must bypass Gatekeeper manually
   - Right-click → Open → Open anyway
   - Not recommended

### Signing with Apple Developer Certificate

If you have a paid Apple Developer account:

1. Install your certificate in Keychain
2. Update `package.json`:
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

3. Build with signing:
   ```bash
   npm run package:mac
   ```

4. Notarize (optional but recommended):
   ```bash
   xcrun notarytool submit dist-builder/*.dmg \
     --apple-id your@email.com \
     --team-id TEAM_ID \
     --password app-specific-password
   ```

---

## Troubleshooting

### Common Build Errors

#### Error: "electron-updater" module not found

**Cause:** Dependencies not installed or out of date

**Fix:**
```bash
cd desktop
rm -rf node_modules package-lock.json
npm install
```

#### Error: "marked" module not found

**Cause:** Missing dependency after git pull

**Fix:**
```bash
cd desktop
npm install
```

#### Error: Icon generation fails

**Cause:** Running script from wrong directory or missing source image

**Fix:**
```bash
cd desktop  # Must be in desktop/ directory
./generate-icons.sh
```

Ensure `Abandoned Upstate.png` exists in project root.

#### Error: Build succeeds but app won't launch

**Cause:** Often related to auto-updater in unsigned builds

**Check logs:**
```bash
# macOS
~/Library/Logs/Abandoned\ Upstate/main.log

# Linux
~/.config/Abandoned\ Upstate/logs/main.log
```

**Common fix:** Ensure auto-updater only runs in production (already fixed in v0.2.0+)

#### Error: "Your app is damaged and can't be opened"

**Cause:** macOS Gatekeeper blocking unsigned app

**Fix:**
```bash
# Remove quarantine attribute
xattr -cr /Applications/Abandoned\ Upstate.app
```

Or right-click → Open → Open anyway

### Debugging Build Issues

#### Enable verbose logging:

```bash
DEBUG=electron-builder npm run package:mac
```

#### Check build configuration:

```bash
npm run build
ls -lh dist-electron/
```

#### Validate package.json:

```bash
npm run test
```

---

## Build Optimization

### Reducing Build Size

Current build size: ~200 MB (typical for Electron apps)

To analyze bundle size:
```bash
npm run build
du -sh dist-electron/
```

### Faster Builds

**Skip code signing during development:**
```bash
CSC_IDENTITY_AUTO_DISCOVERY=false npm run package:mac
```

**Build only your platform:**
```bash
npm run package:mac  # macOS only
npm run package:linux  # Linux only
```

**Use build cache:**
electron-builder automatically caches dependencies in `~/.electron`

---

## Continuous Integration

### GitHub Actions Build

Create `.github/workflows/build.yml`:

```yaml
name: Build Desktop App

on:
  push:
    branches: [main]
    tags:
      - 'v*'

jobs:
  build-mac:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '20'
      - run: cd desktop && npm install
      - run: cd desktop && npm run package:mac
      - uses: actions/upload-artifact@v3
        with:
          name: mac-build
          path: desktop/dist-builder/*.dmg

  build-linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '20'
      - run: cd desktop && npm install
      - run: cd desktop && npm run package:linux
      - uses: actions/upload-artifact@v3
        with:
          name: linux-build
          path: desktop/dist-builder/*.AppImage
```

---

## Release Process

### Creating a Release

1. Update version in `package.json`
2. Update CHANGELOG.md
3. Commit changes:
   ```bash
   git add package.json CHANGELOG.md
   git commit -m "chore: Bump version to 0.2.1"
   ```

4. Create git tag:
   ```bash
   git tag -a v0.2.1 -m "Release v0.2.1"
   git push origin v0.2.1
   ```

5. Build release artifacts:
   ```bash
   npm run package
   ```

6. Create GitHub release:
   ```bash
   gh release create v0.2.1 \
     dist-builder/*.dmg \
     dist-builder/*.zip \
     dist-builder/*.AppImage \
     --title "v0.2.1" \
     --notes "See CHANGELOG.md"
   ```

### Auto-Update Configuration

The app checks for updates at:
- On startup (after 10 seconds)
- Every 4 hours

Updates are fetched from GitHub releases via `electron-updater`.

Configuration in `package.json`:
```json
{
  "build": {
    "publish": {
      "provider": "github",
      "owner": "bizzlechizzle",
      "repo": "aupat"
    }
  }
}
```

---

## Additional Resources

- [electron-builder Documentation](https://www.electron.build/)
- [Electron Security Checklist](https://www.electronjs.org/docs/latest/tutorial/security)
- [macOS Code Signing Guide](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)
- [Self-Signing Guide](./SELF_SIGNING.md)
