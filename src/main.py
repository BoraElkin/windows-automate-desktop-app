from fastapi import FastAPI, Response, HTTPException, Body, Query, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import time
from typing import List, Dict
from .screenshotter import list_windows, screenshot_window, activate_window, get_frontmost_app, get_frontmost_window_windows, get_window_by_id
import pyautogui
import os
import json
import platform
import subprocess
import sys

if getattr(sys, 'frozen', False):
    # Running as a PyInstaller bundle
    ui_dir = os.path.join(sys._MEIPASS, 'ui')
else:
    # Running in dev mode
    ui_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ui')

app = FastAPI()
app.mount("/ui", StaticFiles(directory=ui_dir, html=True), name="ui")
start_time = time.time()

LOG_PATH = os.path.join(os.getcwd(), "app.log")

def log_request(request: Request, response_status: int, payload=None):
    log_entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "endpoint": str(request.url.path),
        "method": request.method,
        "status": response_status,
        "payload": payload,
    }
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    try:
        body = await request.body()
        try:
            payload = body.decode()
        except Exception:
            payload = str(body)
    except Exception:
        payload = None
    response = await call_next(request)
    log_request(request, response.status_code, payload)
    return response

@app.middleware("http")
async def log_requests(request: Request, call_next):
    response = await call_next(request)
    try:
        with open("requests.log", "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {request.method} {request.url.path}\n")
    except Exception:
        pass
    return response

class Bounds(BaseModel):
    x: int
    y: int
    width: int
    height: int

class Window(BaseModel):
    id: str
    title: str
    bounds: Bounds

class AutomateAction(BaseModel):
    x: int
    y: int
    text: str = ""

class AutomateRequest(BaseModel):
    window_id: str
    actions: List[AutomateAction]

@app.get("/")
def root():
    return {"message": "API is running. See /docs for documentation."}

@app.get("/api/v1/health")
def health():
    uptime = int(time.time() - start_time)
    return JSONResponse({"status": "ok", "uptime_seconds": uptime})

@app.get("/api/v1/windows", response_model=List[Window])
def get_windows():
    return list_windows()

@app.get("/api/v1/windows/{window_id}/screenshot")
def get_window_screenshot(window_id: str):
    try:
        png_bytes = screenshot_window(window_id)
        return Response(content=png_bytes, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Window not found or screenshot failed: {e}") 

@app.post("/api/v1/automate")
def automate(req: AutomateRequest):
    prev_app = None
    prev_win = None
    w = get_window_by_id(req.window_id)
    try:
        if platform.system() == "Darwin":
            prev_app = get_frontmost_app()
        elif platform.system() == "Windows":
            prev_win = get_frontmost_window_windows()
        print(f"Activating window {req.window_id}")
        activate_window(req.window_id)
        print("Window activated. Waiting 1 second...")
        time.sleep(1)
        for action in req.actions:
            print(f"Moving to ({action.x}, {action.y}) and clicking")
            pyautogui.moveTo(action.x, action.y)
            pyautogui.click()
            if action.text:
                print(f"Typing: {action.text}")
                pyautogui.typewrite(action.text)
            # Log the action
            with open("dtop_automation.log", "a") as logf:
                logf.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} window_id={req.window_id} x={action.x} y={action.y} text={action.text}\n")
            print(f"Action complete: ({action.x}, {action.y}), text='{action.text}'")
        # Restore previous app (macOS) or window (Windows)
        if prev_app and platform.system() == "Darwin":
            owner = w.get('kCGWindowOwnerName') if isinstance(w, dict) else None
            if prev_app != owner:
                script = f'tell application "{prev_app}" to activate'
                subprocess.run(['osascript', '-e', script])
        elif prev_win and platform.system() == "Windows":
            try:
                prev_win.activate()
            except Exception as e:
                print(f"Error restoring previous window on Windows: {e}")
        print("Automation complete.")
        return {"status": "ok"}
    except Exception as e:
        print(f"Automation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Automation failed: {e}")

@app.get("/api/v1/logs")
def get_logs(limit: int = Query(50, ge=1, le=500)):
    log_path = os.path.join(os.getcwd(), "app.log")
    if not os.path.exists(log_path):
        return []
    with open(log_path, "r") as f:
        lines = f.readlines()[-limit:]
    entries = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except Exception:
            entry = {"raw": line}
        entries.append(entry)
    return entries

@app.get("/api/v1/requests_log")
def get_requests_log(limit: int = 20):
    try:
        with open("requests.log", "r") as f:
            lines = f.readlines()[-limit:]
        return {"log": [line.strip() for line in lines]}
    except Exception as e:
        return {"log": [], "error": str(e)} 