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

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    error "Python 3 is not installed. Please install Python 3.8 or higher."
fi

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
    success "Activated virtual environment"
else
    echo "No virtual environment found. Creating one..."
    python3 -m venv .venv
    source .venv/bin/activate
    success "Created and activated virtual environment"
fi

# Install dependencies if not already installed
if ! pip show pyinstaller > /dev/null 2>&1; then
    echo "Installing dependencies..."
    pip install -r requirements.txt || error "Failed to install dependencies"
    success "Dependencies installed successfully"
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist DTopApp.spec

# Build the app
echo "Building the app..."
pyinstaller --name DTopApp \
            --windowed \
            --onedir \
            --add-data "src:src" \
            --add-data "ui:ui" \
            src/ui.py || error "Failed to build the app"

# Create release directory
echo "Creating release directory..."
mkdir -p release
rm -rf release/*

# Copy the app to release directory
echo "Copying app to release directory..."
cp -r "dist/DTopApp.app" release/

# Create a zip file
echo "Creating zip file..."
cd release
zip -r "DTopApp-macOS.zip" "DTopApp.app"
cd ..

success "Build completed successfully!"
echo "You can find the bundled app in:"
echo "- App bundle: release/DTopApp.app"
echo "- Zip file: release/DTopApp-macOS.zip" 