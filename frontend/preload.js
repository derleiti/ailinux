const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  toggleLlama: () => ipcRenderer.send('toggle-llama'),
  toggleLog: () => ipcRenderer.send('toggle-log'),
});
