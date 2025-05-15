import os
import sys
import time
import pygetwindow as gw
import pyautogui
import mss
import mss.tools
import platform
import subprocess

# --- Window Listing ---
def list_windows():
    windows = []
    seen_ids = set()
    system_keywords = [
        'Control Center', 'Spotlight', 'SystemUIServer', 'Window Server', 'Dock', 'BentoBox', 'Siri', 'NowPlaying', 'KeyboardBrightness', 'Battery', 'WiFi', 'Clock', 'Menubar', 'Item-0'
    ]
    if platform.system() == "Darwin":
        try:
            import Quartz
            cg_windows = Quartz.CGWindowListCopyWindowInfo(
                Quartz.kCGWindowListExcludeDesktopElements | Quartz.kCGWindowListOptionOnScreenOnly,
                Quartz.kCGNullWindowID
            )
            for win in cg_windows:
                title = win.get(Quartz.kCGWindowName, '')
                owner = win.get(Quartz.kCGWindowOwnerName, '')
                # Filter out system UI windows
                if not title and not owner:
                    continue
                if any(keyword in title or keyword in owner for keyword in system_keywords):
                    continue
                wid = str(win.get('kCGWindowNumber'))
                if wid in seen_ids:
                    continue
                seen_ids.add(wid)
                bounds = win.get('kCGWindowBounds', {})
                windows.append({
                    'id': wid,
                    'title': f"{owner} {title}".strip(),
                    'bounds': {
                        'x': bounds.get('X', 0),
                        'y': bounds.get('Y', 0),
                        'width': bounds.get('Width', 0),
                        'height': bounds.get('Height', 0)
                    }
                })
        except Exception as e:
            print(f"Error listing windows on macOS: {e}")
    else:
        titles = gw.getAllTitles()
        for title in titles:
            if not title.strip():
                continue
            win_list = gw.getWindowsWithTitle(title)
            for w in win_list:
                wid = str(w._hWnd) if hasattr(w, '_hWnd') else str(w._handle)
                if wid in seen_ids:
                    continue
                seen_ids.add(wid)
                if w.title and w.isVisible:
                    bounds = {
                        'x': w.left,
                        'y': w.top,
                        'width': w.width,
                        'height': w.height
                    }
                    windows.append({
                        'id': wid,
                        'title': w.title,
                        'bounds': bounds
                    })
    return windows

# --- Window Lookup ---
def get_window_by_id(window_id):
    if platform.system() == "Darwin":
        try:
            import Quartz
            cg_windows = Quartz.CGWindowListCopyWindowInfo(
                Quartz.kCGWindowListExcludeDesktopElements | Quartz.kCGWindowListOptionOnScreenOnly,
                Quartz.kCGNullWindowID
            )
            all_ids = [str(win.get('kCGWindowNumber')) for win in cg_windows]
            for win in cg_windows:
                wid = str(win.get('kCGWindowNumber'))
                if wid == str(window_id):
                    return win
            raise ValueError(f'Window with id {window_id} not found')
        except Exception as e:
            raise ValueError(f'Error getting window by id on macOS: {e}')
    else:
        titles = gw.getAllTitles()
        for title in titles:
            if not title.strip():
                continue
            win_list = gw.getWindowsWithTitle(title)
            for w in win_list:
                wid = str(w._hWnd) if hasattr(w, '_hWnd') else str(w._handle)
                if wid == str(window_id):
                    return w
        raise ValueError(f'Window with id {window_id} not found')

# --- Window Activation ---
def activate_window(window_id):
    if platform.system() == "Darwin":
        # Use AppleScript to activate the window by its owner name (app name)
        try:
            import Quartz
            cg_windows = Quartz.CGWindowListCopyWindowInfo(
                Quartz.kCGWindowListExcludeDesktopElements | Quartz.kCGWindowListOptionOnScreenOnly,
                Quartz.kCGNullWindowID
            )
            for win in cg_windows:
                wid = str(win.get('kCGWindowNumber'))
                if wid == str(window_id):
                    app_name = win.get('kCGWindowOwnerName')
                    if app_name:
                        script = f'tell application "{app_name}" to activate'
                        subprocess.run(['osascript', '-e', script])
                    break
        except Exception as e:
            print(f"Error activating window on macOS: {e}")
    else:
        w = get_window_by_id(window_id)
        w.minimize()
        #time.sleep(0.1)
        w.restore()
        w.activate()
        #time.sleep(0.5)
    return True

# --- Screenshot (cropped to window bounds) ---
def get_frontmost_app():
    script = 'tell application "System Events" to get name of first application process whose frontmost is true'
    result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
    return result.stdout.strip()

def get_frontmost_window_windows():
    # Returns the window object for the current active window on Windows
    try:
        import pygetwindow as gw
        for w in gw.getAllWindows():
            if w.isActive:
                return w
    except Exception as e:
        print(f"Error getting frontmost window on Windows: {e}")
    return None

def screenshot_window(window_id):
    prev_app = None
    prev_win = None
    w = get_window_by_id(window_id)
    if platform.system() == "Darwin":
        prev_app = get_frontmost_app()
    elif platform.system() == "Windows":
        prev_win = get_frontmost_window_windows()
    activate_window(window_id)
    # Re-fetch window in case state changed
    w = get_window_by_id(window_id)
    if 'kCGWindowBounds' in w:  # macOS Quartz window
        bounds = w.get('kCGWindowBounds', {})
        left = bounds.get('X', 0)
        top = bounds.get('Y', 0)
        width = bounds.get('Width', 0)
        height = bounds.get('Height', 0)
    else:  # pygetwindow window
        left = w.left
        top = w.top
        width = w.width
        height = w.height
    with mss.mss() as sct:
        img = sct.grab({'left': left, 'top': top, 'width': width, 'height': height})
        png = mss.tools.to_png(img.rgb, img.size)
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
    return png

# --- Coordinate Mapping Helper ---
def map_relative_to_absolute(window_id, xr, yr, orig_width, orig_height, max_drift=0.2):
    """
    Given window_id, relative coords (xr, yr), and original screenshot size,
    returns (abs_x, abs_y) for automation, with scaling and drift check.
    Throws if window size has changed by > max_drift (fraction).
    """
    w = get_window_by_id(window_id)
    w_cur, h_cur = w.width, w.height
    drift = max(abs(w_cur - orig_width) / orig_width, abs(h_cur - orig_height) / orig_height)
    if drift > max_drift:
        raise RuntimeError(f'Window size drifted by {drift*100:.1f}%, aborting automation.')
    scale_x = w_cur / orig_width
    scale_y = h_cur / orig_height
    abs_x = w.left + xr * scale_x
    abs_y = w.top + yr * scale_y
    return int(abs_x), int(abs_y)