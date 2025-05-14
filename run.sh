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

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if (( $(echo "$PYTHON_VERSION < 3.8" | bc -l) )); then
    error "Python version must be 3.8 or higher. Current version: $PYTHON_VERSION"
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
if ! pip show fastapi > /dev/null 2>&1; then
    echo "Installing dependencies..."
    pip install -r requirements.txt || error "Failed to install dependencies"
    success "Dependencies installed successfully"
fi

# Launch the app
echo "Starting the app..."
python src/ui.py || error "Failed to start the app" 