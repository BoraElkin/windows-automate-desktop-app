# Deployment Guide

This guide explains how to set up, run, and optionally package the DTop App as a desktop application using FastAPI and PyWebview.

---

## 1. Prerequisites
- Python 3.8+
- pip (Python package manager)

---

## 2. Install Dependencies

From the project root directory, run:

```bash
pip install -r requirements.txt
```

---

## 3. Running the App (Development)

To launch the desktop app:

```bash
python src/ui.py
```

- This will start the FastAPI backend and open a native desktop window to the web UI.
- The backend runs at `http://127.0.0.1:8000`.
- The UI is served at `http://127.0.0.1:8000/ui/index.html` (not file://).
- The UI and API must be served from the same origin for full functionality.

**Test the API with curl:**

- Health check:
  ```sh
  curl http://127.0.0.1:8000/api/v1/health
  ```

- List windows:
  ```sh
  curl http://127.0.0.1:8000/api/v1/windows
  ```

- Screenshot a window:
  ```sh
  curl http://127.0.0.1:8000/api/v1/windows/<window_id>/screenshot --output screenshot.png
  ```

- Automate actions:
  ```sh
  curl -X POST http://127.0.0.1:8000/api/v1/automate \
    -H "Content-Type: application/json" \
    -d '{"window_id": "<window_id>", "actions": [{"x": 100, "y": 100, "text": "Hello"}]}'
  ```

- Get logs:
  ```sh
  curl http://127.0.0.1:8000/api/v1/logs
  ```

- Get requests log:
  ```sh
  curl http://127.0.0.1:8000/api/v1/requests_log
  ```

---

## 4. Project Structure

```
/dtop-app
  /src
    main.py         # FastAPI backend
    ui.py           # PyWebview launcher
    ...
  /ui               # Frontend HTML/JS for the UI
  requirements.txt
  DEPLOYMENT.md
```

---

## 5. Packaging as a Standalone Desktop App (Optional)

You can use [PyInstaller](https://pyinstaller.org/) to bundle the app into a single executable:

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```
2. Build the executable:
   ```bash
   pyinstaller --name DTopApp --windowed --onedir --add-data "src:src" --add-data "ui:ui" src/ui.py
   ```
3. The output will be in the `dist/` directory.

**Note:**
- Ensure all static files and models are included or referenced correctly.
- The bundled app now works correctly in both development and bundled modes.

---

## 6. Cross-Platform Notes

- **Windows:** All features should work out of the box.
- **macOS:** Ensure you have the latest Python and Tk (for PyWebview). If you encounter issues, try installing Python via [python.org](https://www.python.org/downloads/).
- **Linux:** You may need to install additional system packages for GUI support (e.g., `libgtk-3-dev`).

---

## 7. Troubleshooting

- If the desktop window does not appear, check your Python and PyWebview installation.
- If the backend does not start, ensure no other process is using port 8000.
- For static file serving, ensure your frontend files are in the `/ui` directory and referenced properly in `main.py`.

---

## 8. Further Customization

- To customize the frontend, edit or add files in the `/ui` directory and update your FastAPI static files configuration if needed.
- For advanced packaging (with icons, splash screens, etc.), refer to the PyInstaller and PyWebview documentation.

---

For questions or issues, please contact the project maintainer. 