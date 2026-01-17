#!/bin/bash

# Build script for EVE Config Copier GitHub releases
# Builds executable for current platform and organizes for release

set -e

echo "Building EVE Config Copier for GitHub release..."

# Get version info
VERSION=${1:-"dev"}
echo "Building version: $VERSION"

# Check if virtual environment is activated (skip in CI/CD environments)
if [[ "$VIRTUAL_ENV" == "" && "$CI" == "" && "$GITHUB_ACTIONS" == "" ]]; then
    echo "Warning: Virtual environment not detected. Attempting to activate..."
    if [ -f "../.venv/bin/activate" ]; then
        source ../.venv/bin/activate
        echo "Activated virtual environment"
    elif [ -f "../venv/bin/activate" ]; then
        source ../venv/bin/activate
        echo "Activated virtual environment"
    else
        echo "No virtual environment found. Assuming CI/CD environment or global Python."
    fi
else
    echo "Using existing Python environment (CI/CD or activated venv)"
fi

# Navigate to project root
cd "$(dirname "$0")/.."

# Install PyInstaller and Pillow if not present
echo "Installing/updating PyInstaller and Pillow..."
pip install pyinstaller pillow

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build/ dist/

# Build the executable
echo "Building executable..."

# Check if icon file exists
ICON_OPTS=""
if [ -f "icon.png" ]; then
    echo "Found icon.png - Pillow will convert to platform-specific format"
    ICON_OPTS="--icon=icon.png"
else
    echo "No icon file found - building without icon"
fi

# Determine platform-specific PyInstaller options
PYINSTALLER_OPTS="--onefile --name EVE-Config-Copier"

# Platform-specific options
if [[ "$PLATFORM" == "windows" ]] || [[ "$OS" == "Windows_NT" ]]; then
    echo "Configuring for Windows build..."
    PYINSTALLER_OPTS="$PYINSTALLER_OPTS --windowed $ICON_OPTS"
    # Windows-specific data separator
    DATA_SEP=";"
elif [[ "$PLATFORM" == "macos" ]] || [[ "$(uname)" == "Darwin" ]]; then
    echo "Configuring for macOS build..."  
    PYINSTALLER_OPTS="$PYINSTALLER_OPTS --windowed $ICON_OPTS"
    # macOS-specific data separator
    DATA_SEP=":"
else
    echo "Configuring for Linux build..."
    PYINSTALLER_OPTS="$PYINSTALLER_OPTS $ICON_OPTS"
    # Linux data separator
    DATA_SEP=":"
fi

# Build data file options
DATA_FILES=""
if [ -f "icon.png" ]; then
    DATA_FILES="$DATA_FILES --add-data icon.png${DATA_SEP}."
fi
if [ -f "README.md" ]; then
    DATA_FILES="$DATA_FILES --add-data README.md${DATA_SEP}."
fi

pyinstaller $PYINSTALLER_OPTS \
    $DATA_FILES \
    --hidden-import="PySide6.QtCore" \
    --hidden-import="PySide6.QtWidgets" \
    --hidden-import="PySide6.QtGui" \
    --hidden-import="requests" \
    --hidden-import="json" \
    --hidden-import="pathlib" \
    --exclude-module="tkinter" \
    --exclude-module="matplotlib" \
    --exclude-module="numpy" \
    --exclude-module="pandas" \
    main.py

# Determine platform info
PLATFORM=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

# Normalize architecture names for consistency
case $ARCH in
    x86_64|amd64) ARCH="x64" ;;
    aarch64|arm64) ARCH="arm64" ;;
    i386|i686) ARCH="x86" ;;
esac

# Normalize platform names
case $PLATFORM in
    darwin) PLATFORM="macos" ;;
    linux) PLATFORM="linux" ;;
    mingw*|msys*|cygwin*) PLATFORM="windows" ;;
esac

DIST_NAME="eve-config-copier-${VERSION}-${PLATFORM}-${ARCH}"
RELEASES_DIR="releases"

echo "Creating release package: ${DIST_NAME}"
mkdir -p "${RELEASES_DIR}/${DIST_NAME}"

# Copy executable based on platform
if [[ "$PLATFORM" == "macos" ]]; then
    if [ -d "dist/EVE-Config-Copier.app" ]; then
        cp -r "dist/EVE-Config-Copier.app" "${RELEASES_DIR}/${DIST_NAME}/"
    else
        cp "dist/EVE-Config-Copier" "${RELEASES_DIR}/${DIST_NAME}/"
    fi
elif [[ "$PLATFORM" == "windows" ]]; then
    cp "dist/EVE-Config-Copier.exe" "${RELEASES_DIR}/${DIST_NAME}/"
else
    cp "dist/EVE-Config-Copier" "${RELEASES_DIR}/${DIST_NAME}/"
fi

# Copy documentation and metadata
cp README.md "${RELEASES_DIR}/${DIST_NAME}/"
cp requirements.txt "${RELEASES_DIR}/${DIST_NAME}/"
cp cleanup.sh "${RELEASES_DIR}/${DIST_NAME}/"

# Create release notes
cat > "${RELEASES_DIR}/${DIST_NAME}/RELEASE_NOTES.txt" << EOF
EVE Config Copier v${VERSION}
Platform: ${PLATFORM^} ${ARCH}
Build Date: $(date)

This is a standalone executable for ${PLATFORM^} ${ARCH}.
No Python installation required.

Usage:
- Run the executable to start the GUI
- First time: Configure EVE directories via Settings
- Use the application to copy configurations between characters

For support and updates: https://github.com/Arcyfa/eve-config-copier

Files included:
- EVE-Config-Copier${PLATFORM:+$([ "$PLATFORM" = "windows" ] && echo ".exe" || [ "$PLATFORM" = "macos" ] && echo ".app")}
- README.md (full documentation)
- requirements.txt (for reference)
- cleanup.sh (utility script)
- RELEASE_NOTES.txt (this file)
EOF

# Create archive
cd "${RELEASES_DIR}"
if command -v zip &> /dev/null; then
    echo "Creating ZIP archive..."
    zip -r "${DIST_NAME}.zip" "${DIST_NAME}/"
    echo "Created: releases/${DIST_NAME}.zip"
fi

if command -v tar &> /dev/null; then
    echo "Creating TAR.GZ archive..."
    tar -czf "${DIST_NAME}.tar.gz" "${DIST_NAME}/"
    echo "Created: releases/${DIST_NAME}.tar.gz"
fi

cd ..

echo ""
echo "✅ Build completed successfully!"
echo "📦 Release package: releases/${DIST_NAME}/"
echo "🗜️  Archives created in releases/ folder"
echo ""
echo "📋 Release info:"
echo "   Version: $VERSION"
echo "   Platform: ${PLATFORM^} ${ARCH}"
echo "   Location: releases/${DIST_NAME}/"
echo ""
echo "🚀 Ready for GitHub release upload!"