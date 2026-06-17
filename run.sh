#!/bin/bash

# DigiNotes Launch Script
# Setup project folder path
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "=== DigiNotes: CS50 Capstone Launcher ==="

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment. Make sure python3-venv is installed."
        exit 1
    fi
fi

# Activate virtual environment and check packages
source .venv/bin/activate

# Check if PySide6-Essentials is installed
python3 -c "import PySide6" &>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install requirements."
        exit 1
    fi
fi

echo "Launching DigiNotes in Wayland/X11 (XCB)..."
# Force XWayland/XCB under Wayland by default to support Stays-on-Top functionality.
# Set DIGINOTES_NATIVE_WAYLAND=1 to force native Wayland.
if [ "$XDG_SESSION_TYPE" = "wayland" ]; then
    if [ "$DIGINOTES_NATIVE_WAYLAND" != "1" ]; then
        export QT_QPA_PLATFORM="xcb"
    fi
fi

python3 src/main.py "$@"
echo "=== DotNotes closed ==="
