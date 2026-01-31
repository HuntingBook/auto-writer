const { app, BrowserWindow } = require('electron');
const path = require('path');

function createWindow() {
    const win = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
        },
        title: "Auto Writer - 智能网文生成系统"
    });

    // Decide if we are in dev or prod based on environment or trial
    // For 'npm run electron' which runs 'vite', we wait for localhost:5173
    // But if the user wants to run against Docker container?
    // We can let them set URL via env var, or default to localhost:5173 (dev) or localhost:3413 (docker)

    const devUrl = 'http://localhost:5173';
    const prodUrl = 'http://localhost:3413'; // Nginx port

    // Simple heuristic: if we are running via npm script that starts vite, we use devUrl.
    // We can check if we can connect to devUrl first, else fallback?
    // OR we just use a command line argument or ENV.

    const contentUrl = process.env.ELECTRON_START_URL || devUrl;

    console.log(`Loading URL: ${contentUrl}`);
    win.loadURL(contentUrl).catch(e => {
        console.log('Failed to load URL, falling back to Docker port (3413)...');
        win.loadURL(prodUrl);
    });
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});
