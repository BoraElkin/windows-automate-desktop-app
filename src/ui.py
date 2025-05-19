#!/usr/bin/env python3
# PyWebview launcher for the FastAPI app
# Starts the FastAPI server and opens a native window to the web UI

import sys
import os
import time
import webview
import subprocess

# Always set the working directory appropriately
if getattr(sys, 'frozen', False):
    # If running as a PyInstaller bundle, set CWD to the bundle directory
    os.chdir(sys._MEIPASS)
else:
    # In dev, set to project root
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if getattr(sys, 'frozen', False):
    # Running as a PyInstaller bundle
    BUNDLE_DIR = sys._MEIPASS
    SRC_PATH = os.path.join(BUNDLE_DIR, 'src')
    PYTHON_EXECUTABLE = sys.executable  # Use the bundled Python
    CWD = BUNDLE_DIR
else:
    # Running in dev mode
    APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    SRC_PATH = os.path.join(APP_ROOT, 'src')
    PYTHON_EXECUTABLE = sys.executable
    CWD = APP_ROOT

# Prepare environment for subprocess to ensure src is importable
env = os.environ.copy()
env['PYTHONPATH'] = os.path.dirname(SRC_PATH) + os.pathsep + env.get('PYTHONPATH', '')

# Path to the minimal UI HTML file
ui_html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../ui/index.html'))

print("Launching FastAPI server...")
server = None
try:
    # Start FastAPI server as a subprocess
    server = subprocess.Popen([
        PYTHON_EXECUTABLE, "-m", "uvicorn", "src.main:app", "--host", "127.0.0.1", "--port", "8000"
    ], cwd=CWD, env=env)  # Set cwd to project root and pass env
    print("Server started, waiting before launching webview...")
    time.sleep(5)  # Increased delay to ensure backend is ready
    print("Launching webview window...")
    # Open the webview window to the served UI
    webview.create_window("Server Monitor", "http://127.0.0.1:8000/ui/index.html")
    webview.start()
except Exception as e:
    print("Exception occurred:", e)
finally:
    print("Shutting down server...")
    # When the window is closed, terminate the server if it was started
    if server is not None:
        try:
            server.terminate()
            server.wait(timeout=5)
        except Exception as e:
            print("Error shutting down server:", e)
    print("Server shut down.") 