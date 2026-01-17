#!/bin/bash

# Build script for EVE Config Copier
# Builds executable for current platform using PyInstaller

set -e

echo "Building EVE Config Copier executable..."

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "Warning: Virtual environment not detected. Attempting to activate..."
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
        echo "Activated virtual environment"
    elif [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        echo "Activated virtual environment"
    else
        echo "No virtual environment found. Please activate manually or run:"
        echo "python -m venv .venv && source .venv/bin/activate"
        exit 1
    fi
fi

# Install PyInstaller if not present
echo "Installing/updating PyInstaller..."
pip install pyinstaller

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build/ dist/ *.spec

# Build the executable
echo "Building executable..."
pyinstaller --onefile \
    --windowed \
    --name "EVE-Config-Copier" \
    --icon="icon.png" \
    --add-data "icon.png:." \
    --add-data "README.md:." \
    --hidden-import="PySide6.QtCore" \
    --hidden-import="PySide6.QtWidgets" \
    --hidden-import="PySide6.QtGui" \
    --exclude-module="tkinter" \
    --exclude-module="matplotlib" \
    --exclude-module="numpy" \
    main.py

# Create platform-specific distribution folder
PLATFORM=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)
DIST_NAME="eve-config-copier-${PLATFORM}-${ARCH}"

echo "Creating distribution: ${DIST_NAME}/"
mkdir -p "${DIST_NAME}"

# Copy executable
if [[ "$PLATFORM" == "darwin" ]]; then
    cp -r "dist/EVE-Config-Copier.app" "${DIST_NAME}/"
else
    cp "dist/EVE-Config-Copier" "${DIST_NAME}/"
fi

# Copy documentation
cp README.md "${DIST_NAME}/"
cp requirements.txt "${DIST_NAME}/"

# Create a simple launcher script for consistency
cat > "${DIST_NAME}/run.sh" << 'EOF'
#!/bin/bash
# Simple launcher for EVE Config Copier
cd "$(dirname "$0")"

if [[ "$OSTYPE" == "darwin"* ]]; then
    open "EVE-Config-Copier.app"
else
    ./EVE-Config-Copier
fi
EOF

chmod +x "${DIST_NAME}/run.sh"

echo "Build completed successfully!"
echo "Distribution created in: ${DIST_NAME}/"
echo ""
echo "Files included:"
ls -la "${DIST_NAME}/"
echo ""
echo "To test the build:"
if [[ "$PLATFORM" == "darwin" ]]; then
    echo "  open '${DIST_NAME}/EVE-Config-Copier.app'"
else
    echo "  cd '${DIST_NAME}' && ./EVE-Config-Copier"
fi