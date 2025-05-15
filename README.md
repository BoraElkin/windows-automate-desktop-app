# FastAPI Desktop Automation App

A cross-platform desktop automation tool with a FastAPI backend. Automate window actions, screenshots, and text input via API.

## Features
- List open windows
- Screenshot any window
- Automate mouse and keyboard actions
- View logs of actions and requests

## Requirements
- Python 3.8 or higher
- (macOS only) Accessibility permissions for your terminal or Python (for automation)

## Setup

```sh
git clone <your-repo-url>
cd <your-repo-directory>
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
bash run.sh
```

## Usage

See interactive API docs at http://localhost:8000/docs

## API Endpoints & Example Usage

### 1. Root Endpoint
**GET /**
```sh
curl http://localhost:8000/
```

---

### 2. Health Check
**GET /api/v1/health**
```sh
curl http://localhost:8000/api/v1/health
```

---

### 3. List Windows
**GET /api/v1/windows**
```sh
curl http://localhost:8000/api/v1/windows
```

---

### 4. Screenshot a Window  
Replace `<window_id>` with the actual window ID.
```sh
curl http://localhost:8000/api/v1/windows/<window_id>/screenshot --output screenshot.png
```

---

### 5. Automate Actions on a Window  
Replace `<window_id>` with the actual window ID.
```sh
curl -X POST http://localhost:8000/api/v1/automate \
  -H "Content-Type: application/json" \
  -d '{
    "window_id": "<window_id>",
    "actions": [
      {"x": 100, "y": 200, "text": "hello"}
    ]
  }'
```

---

### 6. Get App Logs (last 50 entries)
```sh
curl http://localhost:8000/api/v1/logs?limit=50
```

---

### 7. Get Requests Log (last 20 entries)
```sh
curl http://localhost:8000/api/v1/requests_log?limit=20
```

---

### 8. API Documentation (Swagger UI)
Open in your browser:  
http://localhost:8000/docs

## Notes
- On macOS, grant Accessibility permissions to your terminal or Python for automation to work:
  - System Settings → Privacy & Security → Accessibility
- Logs are stored in the `logs/` directory.
- For development, see and edit `src/main.py` for API logic.

## Contributing
Pull requests welcome! Please open an issue first to discuss major changes.

## License
[MIT](LICENSE)

## Building a Standalone App (PyInstaller)

You can build a standalone macOS app bundle using PyInstaller:

### Local Build

```sh
bash build.sh
```
- The app bundle will be in `release/DTopApp.app`
- A zip file for distribution will be in `release/DTopApp-macOS.zip`

### Manual PyInstaller Command

```sh
python3 -m pip install pyinstaller
pyinstaller --name DTopApp \
            --windowed \
            --onedir \
            --add-data "src:src" \
            --add-data "ui:ui" \
            src/ui.py
```

## GitHub Actions: Automated Build & Release

This project includes a GitHub Actions workflow that automatically builds and uploads a macOS app bundle as a release artifact whenever you push a tag starting with `v` (e.g., `v1.0.0`).

- The workflow is defined in `.github/workflows/build.yml`.
- The release artifact will be available as `DTopApp-macOS.zip` in the GitHub release.

## Notes for Releases
- Make sure all changes are committed and pushed before tagging a release.
- Tag a new release with:
  ```sh
  git tag v1.0.0
  git push origin v1.0.0
  ```
- The GitHub Actions workflow will build and upload the release automatically. 