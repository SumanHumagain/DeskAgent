const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let pythonProcess = null;
let isRunningAsAdmin = false;

// Check if running with administrator privileges (Windows only)
function checkAdminStatus() {
    if (process.platform === 'win32') {
        const pythonPath = path.join(__dirname, '..', 'venv', 'Scripts', 'python.exe');
        const scriptPath = path.join(__dirname, '..', 'src', 'api_wrapper.py');

        return new Promise((resolve) => {
            const python = spawn(pythonPath, [scriptPath, '--check-admin']);
            let dataString = '';

            python.stdout.on('data', (data) => {
                dataString += data.toString();
            });

            python.on('close', (code) => {
                try {
                    if (code === 0) {
                        const result = JSON.parse(dataString);
                        resolve(result.is_admin || false);
                    } else {
                        resolve(false);
                    }
                } catch (error) {
                    resolve(false);
                }
            });
        });
    }
    return Promise.resolve(false);
}

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        },
        backgroundColor: '#f0f2f5',
        icon: path.join(__dirname, 'icon.png'), // optional
        autoHideMenuBar: true,
        title: 'Desktop Automation Agent' + (isRunningAsAdmin ? ' [ADMINISTRATOR]' : '')
    });

    mainWindow.loadFile('index.html');

    // Open DevTools in development mode
    if (process.argv.includes('--dev')) {
        mainWindow.webContents.openDevTools();
    }

    mainWindow.on('closed', function () {
        mainWindow = null;
    });

    // Send admin status to renderer after window loads
    mainWindow.webContents.on('did-finish-load', () => {
        mainWindow.webContents.send('admin-status', isRunningAsAdmin);
    });
}

app.whenReady().then(async () => {
    // Check admin status before creating window
    console.log('[ADMIN] Checking administrator privileges...');
    isRunningAsAdmin = await checkAdminStatus();

    if (isRunningAsAdmin) {
        console.log('[ADMIN] ✓ Running with Administrator privileges');
    } else {
        console.log('[ADMIN] ⚠ Running WITHOUT Administrator privileges');
        console.log('[ADMIN] Some operations may fail. Please restart as Administrator.');
    }

    createWindow();

    app.on('activate', function () {
        if (BrowserWindow.getAllWindows().length === 0) createWindow();
    });
});

app.on('window-all-closed', function () {
    if (pythonProcess) {
        pythonProcess.kill();
    }
    if (process.platform !== 'darwin') app.quit();
});

// IPC Handlers

// Handle prompt submission
ipcMain.handle('submit-prompt', async (event, data) => {
    try {
        const { prompt, conversationHistory } = data;
        const result = await executePythonBackend(prompt, conversationHistory || [], false);
        return result;
    } catch (error) {
        return {
            success: false,
            error: error.message
        };
    }
});

// Handle plan approval
ipcMain.handle('approve-plan', async (event, plan) => {
    try {
        const result = await executePlan(plan);
        return result;
    } catch (error) {
        return {
            success: false,
            error: error.message
        };
    }
});

// Handle viewing logs
ipcMain.handle('view-logs', async (event, limit) => {
    try {
        const logs = await getPythonLogs(limit || 10);
        return logs;
    } catch (error) {
        return {
            success: false,
            error: error.message
        };
    }
});

// Handle help request
ipcMain.handle('get-help', async (event) => {
    return {
        success: true,
        help: [
            { title: 'File Operations', examples: ['Open my Downloads folder', 'Find the latest PDF in Documents'] },
            { title: 'File Creation', examples: ['Create a file on Desktop called todo.txt with content "Buy milk"'] },
            { title: 'Advanced', examples: ['Find the 3 largest files in Downloads', 'Email me the report from Downloads'] }
        ]
    };
});

// Handle admin status request
ipcMain.handle('check-admin', async (event) => {
    return {
        success: true,
        is_admin: isRunningAsAdmin
    };
});

// Python Backend Integration Functions

function executePythonBackend(prompt, conversationHistory = [], execute = false) {
    return new Promise((resolve, reject) => {
        const pythonPath = path.join(__dirname, '..', 'venv', 'Scripts', 'python.exe');
        const scriptPath = path.join(__dirname, '..', 'src', 'api_wrapper.py');

        // Check if api_wrapper exists, fallback to direct execution
        const args = [scriptPath, '--prompt', prompt];
        if (!execute) {
            args.push('--plan-only');
        }

        // Add flag to indicate conversation history will be sent via stdin
        if (conversationHistory && conversationHistory.length > 0) {
            args.push('--with-history');
        }

        const python = spawn(pythonPath, args);
        let dataString = '';
        let errorString = '';

        python.stdout.on('data', (data) => {
            dataString += data.toString();
        });

        python.stderr.on('data', (data) => {
            errorString += data.toString();
        });

        python.on('close', (code) => {
            if (code !== 0) {
                reject(new Error(errorString || `Python process exited with code ${code}`));
            } else {
                try {
                    const result = JSON.parse(dataString);
                    resolve(result);
                } catch (error) {
                    reject(new Error('Failed to parse Python output: ' + dataString));
                }
            }
        });

        // Send conversation history via stdin if present
        if (conversationHistory && conversationHistory.length > 0) {
            python.stdin.write(JSON.stringify(conversationHistory));
        }
        python.stdin.end();
    });
}

function executePlan(plan) {
    return new Promise((resolve, reject) => {
        const pythonPath = path.join(__dirname, '..', 'venv', 'Scripts', 'python.exe');
        const scriptPath = path.join(__dirname, '..', 'src', 'api_wrapper.py');

        const args = [scriptPath, '--execute-plan'];

        const python = spawn(pythonPath, args);
        let dataString = '';
        let errorString = '';

        python.stdout.on('data', (data) => {
            dataString += data.toString();
        });

        python.stderr.on('data', (data) => {
            errorString += data.toString();
        });

        python.on('close', (code) => {
            if (code !== 0) {
                reject(new Error(errorString || `Python process exited with code ${code}`));
            } else {
                try {
                    const result = JSON.parse(dataString);
                    resolve(result);
                } catch (error) {
                    reject(new Error('Failed to parse Python output'));
                }
            }
        });

        // Write plan JSON to stdin
        python.stdin.write(JSON.stringify(plan));
        python.stdin.end();
    });
}

function getPythonLogs(limit) {
    return new Promise((resolve, reject) => {
        const pythonPath = path.join(__dirname, '..', 'venv', 'Scripts', 'python.exe');
        const scriptPath = path.join(__dirname, '..', 'src', 'api_wrapper.py');

        const args = [scriptPath, '--get-logs', limit.toString()];

        const python = spawn(pythonPath, args);
        let dataString = '';
        let errorString = '';

        python.stdout.on('data', (data) => {
            dataString += data.toString();
        });

        python.stderr.on('data', (data) => {
            errorString += data.toString();
        });

        python.on('close', (code) => {
            if (code !== 0) {
                reject(new Error(errorString || `Python process exited with code ${code}`));
            } else {
                try {
                    const result = JSON.parse(dataString);
                    resolve(result);
                } catch (error) {
                    reject(new Error('Failed to parse Python output'));
                }
            }
        });
    });
}
