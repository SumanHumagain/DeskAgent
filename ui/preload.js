const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
    submitPrompt: (prompt, conversationHistory) => ipcRenderer.invoke('submit-prompt', { prompt, conversationHistory }),
    approvePlan: (plan) => ipcRenderer.invoke('approve-plan', plan),
    viewLogs: (limit) => ipcRenderer.invoke('view-logs', limit),
    getHelp: () => ipcRenderer.invoke('get-help')
});
