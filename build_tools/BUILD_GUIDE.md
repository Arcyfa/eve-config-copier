# Build and Release Guide

This guide explains how to build and release EVE Config Copier executables.

## Important: PyInstaller Platform Limitations

**⚠️ PyInstaller can ONLY build for the platform it runs on:**
- **Linux** machine → builds Linux executable
- **Windows** machine → builds Windows executable  
- **macOS** machine → builds macOS executable

**You cannot cross-compile between platforms with PyInstaller.**

## Folder Structure

```
eve-config-copier/
├── build_tools/           # Build scripts and configurations
│   ├── build_for_release.sh    # Main release build script
│   ├── build_executable.sh     # Simple build script
│   ├── eve_config_copier.spec  # PyInstaller spec file
│   └── pyinstaller_utils.py    # Utilities for bundled apps
├── releases/              # Built executables ready for distribution
│   ├── eve-config-copier-v1.0.0-linux-x64/
│   ├── eve-config-copier-v1.0.0-windows-x64.zip
│   └── eve-config-copier-v1.0.0-macos-arm64.tar.gz
└── .github/workflows/     # Automated GitHub Actions builds
    └── build-releases.yml
```

## Local Building

### Option 1: Quick Build
```bash
# Simple build for development/testing
cd build_tools/
./build_executable.sh
```

### Option 2: Release Build
```bash
# Professional release build with proper packaging
./build_tools/build_for_release.sh v1.0.0
```

This creates:
- `releases/eve-config-copier-v1.0.0-[platform]-[arch]/` folder
- `releases/eve-config-copier-v1.0.0-[platform]-[arch].zip` archive
- `releases/eve-config-copier-v1.0.0-[platform]-[arch].tar.gz` archive

## Cross-Platform Building

### Method 1: Manual (Recommended for control)

**Build on each platform separately:**

1. **On Linux machine:**
   ```bash
   ./build_tools/build_for_release.sh v1.0.0
   # Creates: releases/eve-config-copier-v1.0.0-linux-x64.tar.gz
   ```

2. **On Windows machine:**
   ```bash
   ./build_tools/build_for_release.sh v1.0.0
   # Creates: releases/eve-config-copier-v1.0.0-windows-x64.zip
   ```

3. **On macOS machine:**
   ```bash
   ./build_tools/build_for_release.sh v1.0.0  
   # Creates: releases/eve-config-copier-v1.0.0-macos-arm64.tar.gz
   ```

### Method 2: GitHub Actions (Automatic)

**Automated cross-platform building with repository commits:**

1. **For tagged releases:**
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
   
2. **For manual builds:**
   - Go to GitHub Actions tab
   - Click "Build Releases" workflow
   - Click "Run workflow"
   - Enter version number
   
GitHub Actions will automatically:
- Build on Linux, Windows, and macOS runners in parallel
- **Verify all three builds completed successfully**  
- **Commit build files back to the repository** (in `releases/` folder)
- Create GitHub release **only if all builds succeed**
- Upload all builds to GitHub releases
- Generate professional release notes

**Build Safety:** The release is only created if all three platform builds are successful. If any platform fails, no release is published and no files are committed.

## GitHub Release Workflow

### Automatic Release (Recommended)
1. **Create and push a version tag:**
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. **GitHub Actions will automatically:**
   - Build for all 3 platforms in parallel
   - **Verify all builds completed successfully**
   - **Commit build files to repository** (`releases/` folder)
   - Create GitHub release **only if all 3 builds succeed**
   - Upload all executables to the release
   - Generate professional release notes

3. **Safety guarantees:**
   - ❌ If any platform build fails → No release created, no files committed
   - ✅ Only when all 3 builds succeed → Files committed + release published
   - 🔄 Build files are permanently stored in the repository for version history

### Manual Release
1. **Build locally** (on each platform)
2. **Upload to GitHub:**
   - Go to repository → Releases
   - Click "Create a new release"  
   - Create tag (e.g., `v1.0.0`)
   - Upload your built `.zip`/`.tar.gz` files
   - Add release notes

## File Naming Convention

Built executables follow this pattern:
```
eve-config-copier-[version]-[platform]-[arch].[extension]
```

Examples:
- `eve-config-copier-v1.0.0-linux-x64.tar.gz`
- `eve-config-copier-v1.0.0-windows-x64.zip`  
- `eve-config-copier-v1.0.0-macos-arm64.tar.gz`
- `eve-config-copier-dev-linux-x64.tar.gz` (development build)

## Testing Builds

Before releasing, test on each target platform:

1. **Extract the archive**
2. **Run the executable**  
3. **Test core functionality:**
   - GUI loads correctly
   - Settings dialog works
   - File operations work
   - Cross-platform paths detected

## Release Checklist

- [ ] Update version in code/docs
- [ ] Test locally on development platform
- [ ] Create git tag with version
- [ ] Push tag to trigger automated builds
- [ ] Wait for GitHub Actions to complete
- [ ] Verify all 3 platform builds were created
- [ ] Download and test each platform executable
- [ ] Update release notes if needed
- [ ] Announce release

## Architecture Support

Current builds target:
- **Linux**: x64 (Intel/AMD 64-bit)  
- **Windows**: x64 (Intel/AMD 64-bit)
- **macOS**: arm64 (Apple Silicon) and x64 (Intel Mac)

Additional architectures can be added by modifying the build scripts.