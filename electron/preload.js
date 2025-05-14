const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  getWindows: () => ipcRenderer.invoke('get-windows'),
  captureWindow: (sourceId) => ipcRenderer.invoke('capture-window', sourceId),
  ingest: (payload) => ipcRenderer.invoke('ingest', payload),
  automateInput: (payload) => ipcRenderer.invoke('automate-input', payload),
  onShowFieldConfirm: (callback) => ipcRenderer.on('show-field-confirm', (_event, args) => callback(args)),
  sendFieldConfirmResponse: (choice) => ipcRenderer.send('field-confirm-response', choice),
  sendOverlayReady: () => ipcRenderer.send('overlay-ready'),
  updateWriteCoordinates: (coords) => ipcRenderer.invoke('update-write-coordinates', coords),
});
