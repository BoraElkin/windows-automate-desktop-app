import { app, BrowserWindow, ipcMain, protocol, session as electronSession, desktopCapturer, nativeImage, dialog, screen } from 'electron';
// import serve from 'electron-serve'; // No longer needed for static serving
import path from 'node:path';
import { fileURLToPath } from 'node:url'; // Import fileURLToPath
// import { runNextJs } from 'next-electron-rsc/main'; // Original import
import { createHandler } from 'next-electron-rsc'; // Use named import for createHandler
import { spawn } from 'child_process';
import robot from 'robotjs';
import { windowManager } from 'node-window-manager';

// Calculate __dirname equivalent for ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Variable to store custom coordinates from dragged bubble
let customWriteCoordinates = null;

// Add handler to receive updated coordinates
ipcMain.handle('update-write-coordinates', (_event, coords) => {
  console.log('Received updated write coordinates:', coords);
  customWriteCoordinates = coords;
  return true;
});

// const isDev = !app.isPackaged; // createHandler handles dev/prod detection
// const loadURL = isDev
//   ? 'http://localhost:3000'
//   : serve({ directory: 'out' });

// --- Initialize next-electron-rsc Handler BEFORE app is ready ---
const projectDir = path.join(__dirname, '../');
console.log(`Initializing Next.js handler for directory: ${projectDir}`);
const { createInterceptor, localhostUrl } = createHandler({
  protocol: protocol,             // Pass Electron's protocol module
  dir: projectDir,                // Pass project root directory
  dev: true,                      // Force dev mode for development server
  debug: true,                    // Enable debug logs for next-electron-rsc
  port: 3001,                     // Explicitly use port 3001 to avoid port 3000 conflicts
  // hostname: 'localhost',      // Optional: defaults to localhost
  // port: 3000,                // Optional: defaults to 3000
});
console.log(`Next.js handler initialized. Target URL: ${localhostUrl}`);
// ---------------------------------------------------------------

let mainWindow = null;
let stopIntercept; // To store the interceptor cleanup function
let fieldConfirmOverlayWindow = null;

async function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      session: electronSession.defaultSession,
    },
  });

  try {
    // Handler is already initialized above

    // Setup the interceptor using the window's session
    stopIntercept = await createInterceptor({
      session: mainWindow.webContents.session, // Use the window's specific session
    });
    console.log('HTTP protocol interception enabled.');

    // Load the URL provided by the handler
    await mainWindow.loadURL(localhostUrl);
    // Open developer tools automatically to inspect frontend errors
    mainWindow.webContents.openDevTools({ mode: 'detach' });
    // Log load failures for further debugging
    mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription, validatedURL, isMainFrame) => {
      console.error('Window failed to load:', { errorCode, errorDescription, validatedURL, isMainFrame });
    });
    console.log(`Loaded URL: ${localhostUrl}`);

  } catch (error) {
    console.error('Failed during interceptor setup or loading URL:', error);
    // Optionally load a fallback error page
    // mainWindow.loadFile('path/to/error.html');
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
    // Clean up the interceptor when the window closes - REMOVED FROM HERE
    // if (stopIntercept) {
    //   stopIntercept();
    //   console.log('HTTP protocol interception stopped.');
    // }
  });
}

// --- App Lifecycle --- 

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.on('ready', createWindow);

// Quit when all windows are closed, except on macOS.
app.on('window-all-closed', () => {
  // On macOS it is common for applications and their menu bar
  // to stay active until the user quits explicitly with Cmd + Q.
  if (process.platform !== 'darwin') {
    // Ensure interceptor is cleaned up on quit - MOVED TO will-quit
    // if (stopIntercept) {
    //   stopIntercept();
    // }
    app.quit();
  }
});

// Added: Cleanup interceptor before quitting
app.on('will-quit', () => {
  if (stopIntercept) {
    stopIntercept();
    console.log('HTTP protocol interception stopped before quit.');
  }
});

app.on('activate', () => {
  // On macOS it's common to re-create a window in the app when the
  // dock icon is clicked and there are no other windows open.
  if (mainWindow === null) {
    createWindow();
  }
});

// --- Custom IPC Handlers ---

// Get list of available windows (excluding the current app)
ipcMain.handle('get-windows', async () => {
  const sources = await desktopCapturer.getSources({ types: ['window'], thumbnailSize: { width: 0, height: 0 } });
  const appName = app.getName();
  return sources
    .filter(source => source.name && source.name !== appName) // Filter out unnamed windows and the app itself
    .map(source => ({ id: source.id, name: source.name }));
});

// Capture a specific window by sourceId and return as Data URL
ipcMain.handle('capture-window', async (event, sourceId) => {
  if (!mainWindow) {
    throw new Error('Main window not available');
  }

  try {
    // Fetch the specific source to get a potentially larger thumbnail
    const sources = await desktopCapturer.getSources({ types: ['window'], thumbnailSize: { width: 1920, height: 1080 } }); // Request a decent size thumbnail
    const source = sources.find(s => s.id === sourceId);

    if (!source) {
      throw new Error(`Window source with ID ${sourceId} not found.`);
    }

    // Find the real window by title (best effort)
    let winBounds = null;
    let winTitle = source.name;
    const windows = windowManager.getWindows();
    const match = windows.find(w => w.getTitle() && w.getTitle().trim() === winTitle.trim());
    if (match) {
      winBounds = match.getBounds();
    }

    const screenshot = source.thumbnail; // This is a NativeImage
    const dataUrl = screenshot.toDataURL(); // Convert to PNG Data URL
    const filename = `window_screenshot_${Date.now()}.png`;
    const contentType = 'image/png';
    // Assume thumbnailSize is 1920x1080
    const imageWidth = 1920;
    const imageHeight = 1080;

    // Ensure the main application window is focused after capture
    mainWindow.focus();

    return { dataUrl, name: filename, contentType, bounds: winBounds, imageWidth, imageHeight };
  } catch (error) {
    console.error('Failed to capture window:', error);
    mainWindow.focus(); // Ensure focus returns even on error
    throw error; // Re-throw the error to be caught by the renderer
  }
});

// Add ingest IPC handler
ipcMain.handle('ingest', async (_evt, payload) => {
  return new Promise((resolve, reject) => {
    const script = path.join(__dirname, 'python', 'ingest.py');

    // Separate payload: data_to_write as arg, screenshot via stdin
    const { screenshot, data_to_write } = payload;
    if (!screenshot || !data_to_write) {
      return reject(new Error('Invalid payload: missing screenshot or data_to_write'));
    }

    const args = [JSON.stringify(data_to_write)]; // Pass data_to_write as arg
    const proc = spawn('python', [script, ...args], {
      stdio: ['pipe', 'pipe', 'pipe'], // Enable stdin/stdout/stderr piping
    });

    let stdout = '';
    let stderr = '';
    proc.stdout.on('data', (data) => { stdout += data; });
    proc.stderr.on('data', (data) => { stderr += data; });

    proc.on('close', (code) => {
      if (code !== 0) {
        console.error('Python ingest error:', stderr);
        return reject(new Error(`Python exited with code ${code}\nStderr: ${stderr}`));
      }
      try {
        const result = JSON.parse(stdout);
        resolve(result);
      } catch (e) {
        console.error('Failed to parse Python output:', stdout);
        reject(new Error(`Failed to parse Python output: ${e.message}`));
      }
    });

    proc.on('error', (err) => {
      console.error('Failed to start Python subprocess:', err);
      reject(new Error(`Failed to start Python subprocess: ${err.message}`));
    });

    // Write screenshot data URI to Python script's stdin
    proc.stdin.write(screenshot);
    proc.stdin.end(); // Close stdin to signal end of input
  });
});

// Helper to pause execution for a given number of milliseconds
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// Add helper to show a per-field confirmation popup
async function showFieldConfirmWindow(x, y, text) {
  return new Promise((resolve) => {
    ipcMain.once('field-confirm-response', (_event, choice) => {
      // Close overlay when a choice is made
      if (fieldConfirmOverlayWindow) {
        fieldConfirmOverlayWindow.close();
        fieldConfirmOverlayWindow = null;
      }
      resolve(choice);
    });
    // Create an overlay window covering the entire display
    const { bounds } = screen.getPrimaryDisplay();
    fieldConfirmOverlayWindow = new BrowserWindow({
      x: bounds.x,
      y: bounds.y,
      width: bounds.width,
      height: bounds.height,
      frame: false,
      transparent: true,
      backgroundColor: '#00000000',
      alwaysOnTop: true,
      skipTaskbar: true,
      focusable: true,
      resizable: false,
      hasShadow: false,
      webPreferences: {
        preload: path.join(__dirname, 'preload.js'),
        contextIsolation: true,
        nodeIntegration: false,
      },
    });
    // Open DevTools for the overlay for debugging
    fieldConfirmOverlayWindow.webContents.openDevTools({ mode: 'detach' });
    // Load overlay page and send bubble data once React is ready
    // Handshake: wait for overlay renderer to signal readiness, then send confirm data
    ipcMain.once('overlay-ready', () => {
      if (fieldConfirmOverlayWindow) {
        fieldConfirmOverlayWindow.webContents.send('show-field-confirm', { x, y, text });
        fieldConfirmOverlayWindow.focus();
      }
    });
    // Load the overlay page to render the bubble component
    fieldConfirmOverlayWindow.loadURL(`${localhostUrl}/overlay`);
  });
}

// Add automate-input IPC handler to simulate input using robotjs
ipcMain.handle('automate-input', async (_evt, payload) => {
  console.log('Received automate-input payload:', JSON.stringify(payload, null, 2));
  const { mapping, bbox_dict, data_to_write, sourceId, bounds, imageWidth, imageHeight } = payload;
  let targetWindowActivated = false;
  
  // Activate the target window first
  console.log('[Automate] Attempting to activate target window...');
  try {
    // Find the window by its source ID
    const sources = await desktopCapturer.getSources({ types: ['window'], thumbnailSize: { width: 0, height: 0 } });
    const targetSource = sources.find(s => s.id === sourceId);
    
    if (!targetSource) {
      console.warn('[Automate] Target window not found, automation may not work correctly');
    } else {
      console.log(`[Automate] Activating window: ${targetSource.name}`);
      // On Windows, we can use powerShell commands to activate windows
      if (process.platform === 'win32') {
        const ps = spawn('powershell.exe', [
          '-command',
          `(New-Object -ComObject WScript.Shell).AppActivate('${targetSource.name.replace(/'/g, "''")}')`
        ]);
        // Wait for the window activation to take effect
        await sleep(500); // Increased sleep time for activation
        targetWindowActivated = true; // Assume activation worked for now
        console.log('[Automate] Window activation command sent.');
      } else {
        console.log('[Automate] Window activation only implemented for Windows currently.');
      }
      // Note: For macOS and Linux, window activation methods would differ
      // and would need to be implemented separately
    }
  } catch (error) {
    console.error('[Automate] Failed to activate target window:', error);
    // Continue with automation attempt even if activation fails
  }
  
  if (!targetWindowActivated) {
    console.warn('[Automate] Target window might not be active. Input might go to the wrong window.');
  }
  
  // Iterate over each box ID in the mapping
  console.log('[Automate] Starting input automation loop...');
  for (const [boxId, value] of Object.entries(mapping)) {
    const bbox = bbox_dict[boxId];
    console.log(`[Automate] Processing field - ID: ${boxId}, Value: "${value}"`);
    
    if (!Array.isArray(bbox) || bbox.length !== 4) {
      console.warn(`[Automate] Invalid bounding box for box ID ${boxId}:`, bbox);
      continue;
    }
    
    // Calculate center coordinates in image space
    const [x1, y1, x2, y2] = bbox.map((n) => Number(n));
    const x_mid = Math.round((x1 + x2) / 2);
    const y_mid = Math.round((y1 + y2) / 2);
    // Map to real screen coordinates using window bounds
    let mouseX = x_mid;
    let mouseY = y_mid;
    if (bounds && imageWidth && imageHeight) {
      mouseX = Math.round(bounds.x + (x_mid / imageWidth) * bounds.width);
      mouseY = Math.round(bounds.y + (y_mid / imageHeight) * bounds.height);
      console.log(`[Automate] Mapped to screen coordinates: (${mouseX}, ${mouseY}) using bounds`, bounds);
    } else {
      console.warn('[Automate] Missing bounds or image size, using raw image coordinates.');
    }
    
    // Skip showing confirmation bubbles but keep coordinates calculation
    // const choice = await showFieldConfirmWindow(x_mid, y2 + 5, String(value));
    
    // Move mouse to field center
    console.log(`[Automate] Moving mouse to (${mouseX}, ${mouseY})...`);
    robot.moveMouse(mouseX, mouseY);
    await sleep(10); // Short delay after moving
    console.log(`[Automate] Clicking at (${mouseX}, ${mouseY})...`);
    robot.mouseClick();
    await sleep(10); // Slightly longer delay after click to allow focus
    console.log(`[Automate] Typing string: "${String(value)}"...`);
    robot.typeString(String(value));
    console.log(`[Automate] Finished typing for field ID ${boxId}.`);
    // Small delay before next field
    await sleep(20); // Increased delay between fields
  }
  console.log('[Automate] Automation routine completed.');
});

// Optional: Add any IPC handlers needed for Electron-specific features
// ipcMain.handle('some-electron-feature', async (event, args) => {
//   // ...
// });
