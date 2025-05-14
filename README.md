# Screenshot-Automate Desktop App

A FastAPI-based backend for desktop window automation and screenshotting, designed for integration with a web frontend and AI-driven workflows.

---

## Quick Start

### Option 1: Download Latest Release (Recommended for Users)

1. Go to the [Releases](https://github.com/yourusername/dtop-app/releases) page
2. Download the latest `DTopApp-macOS.zip`
3. Extract the zip file
4. Double-click `DTopApp.app` to run

**Note:** The app is automatically built and released when we push a new version tag.

### Option 2: Run from Source (For Developers)

```sh
./run.sh
```

---

## Features

- **Health check endpoint**
- **List open user-facing windows** (filtered for relevance)
- **Take screenshots of any open window**
- **Automate mouse clicks and typing in any window**
- **(Planned) Retrieve automation logs**

---

## API Endpoints

### 1. `GET /api/v1/health`
**Description:**  
Returns the health status and uptime of the server.

**Response:**
```json
{
  "status": "ok",
  "uptime_seconds": 123
}
```

**Test with curl:**
```sh
curl http://127.0.0.1:8000/api/v1/health
```

---

### 2. `GET /api/v1/windows`
**Description:**  
Lists all open, user-facing windows with their IDs, titles, and bounds.

**Response:**
```json
[
  {
    "id": "394",
    "title": "Notes Test",
    "bounds": { "x": 100, "y": 100, "width": 800, "height": 600 }
  },
  ...
]
```

**Test with curl:**
```sh
curl http://127.0.0.1:8000/api/v1/windows
```

---

### 3. `GET /api/v1/windows/{window_id}/screenshot`
**Description:**  
Returns a PNG screenshot of the specified window's client area.

**Response:**  
- `image/png` binary data

**Test with curl:**
```sh
curl http://127.0.0.1:8000/api/v1/windows/<window_id>/screenshot --output screenshot.png
```

---

### 4. `POST /api/v1/automate`
**Description:**  
Automates actions (mouse clicks and typing) in a specified window.

**Request Body:**
```json
{
  "window_id": "394",
  "actions": [
    { "x": 600, "y": 200, "text": "Hello World" }
  ]
}
```
- Brings the window to the front.
- For each action: moves mouse, clicks, and types text if provided.

**Response:**
```json
{ "status": "ok" }
```

**Test with curl:**
```sh
curl -X POST http://127.0.0.1:8000/api/v1/automate \
  -H "Content-Type: application/json" \
  -d '{"window_id": "<window_id>", "actions": [{"x": 100, "y": 100, "text": "Hello"}]}'
```

---

### 5. `GET /api/v1/logs?limit=N`
**Description:**  
Returns the last N log entries from the automation log.

**Test with curl:**
```sh
curl http://127.0.0.1:8000/api/v1/logs
```

---

### 6. `GET /api/v1/requests_log`
**Description:**  
Returns the last N entries from the requests log.

**Test with curl:**
```sh
curl http://127.0.0.1:8000/api/v1/requests_log
```

---

## Setup & Requirements

- **Python 3.8+**
- **macOS or Windows** (cross-platform support)
- **Dependencies:**  
  - `fastapi`
  - `uvicorn`
  - `pygetwindow`
  - `pyautogui`
  - `mss`
  - `pydantic`
  - `pywebview`

Install dependencies:
```sh
pip install -r requirements.txt
```

---

## Running the Server and UI

```sh
python src/ui.py
```

- This will start the FastAPI backend and open a native desktop window to the web UI.
- The backend runs at `http://127.0.0.1:8000`.
- The UI is served at `http://127.0.0.1:8000/ui/index.html` (not file://).
- The UI and API must be served from the same origin for full functionality.

---

## Project Structure

```
/dtop-app
  /src
    main.py         # FastAPI backend
    ui.py           # PyWebview launcher
    ...
  /ui               # Frontend HTML/JS for the UI
  requirements.txt
  README.md
  run.sh
```

---

## Notes

- **macOS:**  
  - Grant Accessibility permissions to your terminal or Python app for automation to work.
  - Some system UI windows are filtered out for a cleaner window list.
- **Window IDs:**  
  - IDs may change if you close/reopen windows. Always fetch the latest list before automating.
- **Automation:**  
  - Coordinates are absolute screen positions. Use screenshots to determine the correct values.
- **Bundled App:**  
  - The app is now bundled with PyInstaller and works correctly in both development and bundled modes.

---

## Contributing

- Keep code simple and DRY.
- Avoid code duplication and unnecessary mocking.
- Keep files under 200–300 lines; refactor as needed.
- Do not add stubbing or fake data to dev/prod code.

---

## License

MIT 

## Building the App

### For Users
Simply download the latest release from the [Releases](https://github.com/BoraElkin/ss-desktop-app/releases) page.

### For Developers
If you want to build the app yourself:

1. Clone the repository:
   ```sh
   git clone https://github.com/yourusername/dtop-app.git
   cd dtop-app
   ```

2. Run the build script:
   ```sh
   ./build.sh
   ```

3. The bundled app will be in the `release` directory:
   - `release/DTopApp.app` - The macOS application bundle
   - `release/DTopApp-macOS.zip` - A zip file containing the app

### Creating a New Release
To create a new release:

1. Update the version in your code
2. Create and push a new tag:
   ```sh
   git tag v1.0.0  # Use appropriate version number
   git push origin v1.0.0
   ```
3. GitHub Actions will automatically build and create a new release 