# Desktop Automation Agent - Electron UI

A beautiful Electron-based graphical user interface for the Desktop Automation Agent.

## Features

- 🎨 Modern, gradient-styled interface
- 📝 Text input box for natural language prompts
- ✅ Visual plan approval workflow
- 📊 Real-time execution feedback
- 📜 Built-in log viewer
- 🔄 Status indicators and timestamps

## Installation

### 1. Install Node.js Dependencies

Navigate to the `ui` directory and install dependencies:

```bash
cd ui
npm install
```

### 2. Ensure Python Backend is Set Up

Make sure the Python backend is properly configured:

```bash
cd ..
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Configure your `.env` file with your OpenAI API key.

## Usage

### Running the Application

From the `ui` directory:

```bash
npm start
```

Or for development mode with DevTools:

```bash
npm run dev
```

### Using the Interface

1. **Enter a Command**: Type your natural language command in the input box
   - Example: "Open my Downloads folder"
   - Example: "Find the latest PDF in Documents"

2. **Review the Plan**: The AI will create a plan and show you the actions

3. **Approve or Cancel**:
   - Click ✓ Execute to run the actions
   - Click ✗ Cancel to reject the plan

4. **View Results**: See the execution results in the output area

### Additional Features

- **Help Button**: Click to see example commands
- **View Logs**: Click to see recent action history
- **Clear Button**: Clear the output area

## Architecture

```
┌─────────────────┐
│  Electron UI    │
│  (index.html)   │
└────────┬────────┘
         │
┌────────▼────────┐
│  Renderer.js    │  (UI logic)
└────────┬────────┘
         │ IPC
┌────────▼────────┐
│   Main.js       │  (Electron main process)
└────────┬────────┘
         │ Child Process
┌────────▼────────┐
│  api_wrapper.py │  (Python API)
└────────┬────────┘
         │
┌────────▼────────┐
│ Python Backend  │  (Planner, Executor, etc.)
└─────────────────┘
```

## Development

### File Structure

```
ui/
├── index.html      # Main UI layout and styles
├── main.js         # Electron main process
├── preload.js      # IPC security bridge
├── renderer.js     # UI logic and event handlers
├── package.json    # Node.js dependencies
└── README.md       # This file
```

### Key Technologies

- **Electron**: Desktop application framework
- **Node.js**: JavaScript runtime
- **IPC (Inter-Process Communication)**: Secure communication between UI and main process
- **Child Process**: Spawning Python backend
- **Context Isolation**: Security feature to protect renderer process

## Troubleshooting

### "Python process exited with code 1"

- Make sure your Python virtual environment is activated
- Check that `src/api_wrapper.py` exists
- Verify your `.env` file has a valid OpenAI API key

### UI not loading

- Check that you ran `npm install` first
- Try clearing Electron cache: Delete `%APPDATA%\desktop-automation-agent-ui`

### Actions not executing

- Verify `config/allowlist.json` includes the necessary paths
- Check the logs using the "View Logs" button
- Look for error messages in the output area

## Security

- **Context Isolation**: Enabled to prevent renderer from accessing Node.js APIs
- **Node Integration**: Disabled for security
- **Preload Script**: Uses secure IPC bridge for communication
- **No Direct Backend Access**: All Python calls go through controlled IPC handlers

## Future Enhancements

- [ ] Dark mode toggle
- [ ] Custom themes
- [ ] System tray integration
- [ ] Voice input support
- [ ] Progress indicators for long-running tasks
- [ ] Export logs to file
- [ ] Settings panel for configuration
- [ ] Keyboard shortcuts

## License

MIT License
