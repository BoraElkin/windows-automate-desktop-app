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
    w = get_window_by_id(window_id)
    w.minimize()
    w.restore()
    w.activate()
    return True

# --- Get Frontmost Window (Windows) ---
def get_frontmost_window_windows():
    try:
        for w in gw.getAllWindows():
            if w.isActive:
                return w
    except Exception as e:
        print(f"Error getting frontmost window on Windows: {e}")
    return None

# --- Screenshot (cropped to window bounds) ---
def screenshot_window(window_id):
    prev_win = get_frontmost_window_windows()
    w = get_window_by_id(window_id)
    activate_window(window_id)
    # Re-fetch window in case state changed
    w = get_window_by_id(window_id)
    left = w.left
    top = w.top
    width = w.width
    height = w.height
    with mss.mss() as sct:
        img = sct.grab({'left': left, 'top': top, 'width': width, 'height': height})
        png = mss.tools.to_png(img.rgb, img.size)
    # Restore previous window
    if prev_win:
        try:
            prev_win.activate()
        except Exception as e:
            print(f"Error restoring previous window on Windows: {e}")
    return png

# --- Coordinate Mapping Helper ---
def map_relative_to_absolute(window_id, xr, yr, orig_width, orig_height, max_drift=0.2):
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