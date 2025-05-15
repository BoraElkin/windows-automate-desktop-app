#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Function to print error messages
error() {
    echo -e "${RED}Error: $1${NC}" >&2
    exit 1
}

# Function to print success messages
success() {
    echo -e "${GREEN}$1${NC}"
}

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    error "Python 3 is not installed. Please install Python 3.8 or higher."
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if (( $(echo "$PYTHON_VERSION < 3.8" | bc -l) )); then
    error "Python version must be 3.8 or higher. Current version: $PYTHON_VERSION"
fi

# Create and activate virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "No virtual environment found. Creating one..."
    python3 -m venv .venv || error "Failed to create virtual environment"
    success "Created virtual environment"
fi
source .venv/bin/activate || error "Failed to activate virtual environment"
success "Activated virtual environment"

# Upgrade pip
python3 -m pip install --upgrade pip || error "Failed to upgrade pip"

# Install dependencies
python3 -m pip install -r requirements.txt || error "Failed to install dependencies"
python3 -m pip install pyinstaller || error "Failed to install PyInstaller"
success "Dependencies installed successfully"

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist DTopApp.spec release/*

# Build the app
echo "Building the app with PyInstaller..."
pyinstaller --name DTopApp \
            --windowed \
            --onedir \
            --add-data "src:src" \
            --add-data "ui:ui" \
            --hidden-import=uvicorn \
            --hidden-import=fastapi \
            --hidden-import=starlette \
            --hidden-import=pydantic \
            --hidden-import=requests \
            --hidden-import=webview \
            --hidden-import=pyautogui \
            src/ui.py || error "Failed to build the app"

# Codesign the app with entitlements
if [ -d "dist/DTopApp.app" ]; then
    echo "Codesigning the app with entitlements..."
    codesign --entitlements entitlements.plist --deep --force --sign - dist/DTopApp.app || error "Codesigning failed. See above for details."
    success "Codesigning completed."
fi

# Create release directory
mkdir -p release

# Copy the app to release directory
if [ -d "dist/DTopApp.app" ]; then
    cp -r "dist/DTopApp.app" release/
    cd release
    zip -r "DTopApp-macOS.zip" "DTopApp.app"
    cd ..
    success "Build completed successfully!"
    echo "You can find the bundled app in:"
    echo "- App bundle: release/DTopApp.app"
    echo "- Zip file: release/DTopApp-macOS.zip"
else
    error "Build failed: DTopApp.app not found in dist/"
fi 