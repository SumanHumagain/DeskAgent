# Desktop Automation Agent

AI-powered desktop automation tool that executes natural language commands to control your Windows PC.

## Overview

This tool allows you to control your computer using natural language prompts. It uses an LLM to convert your requests into structured actions, then executes them safely with confirmation and audit logging.

**Example prompts:**
- "Open my Downloads folder and find the latest PDF"
- "Create a new text file on Desktop called notes.txt and write 'Meeting at 3pm'"
- "Email me the 3 largest files from my Documents folder"

## User Interfaces

### 🎨 Electron GUI (Recommended)

A modern graphical interface with:
- Text input box for prompts
- Visual plan approval workflow
- Real-time execution feedback
- Built-in log viewer

**Quick Start:**
```bash
cd ui
npm install
npm start
```

See [ui/README.md](ui/README.md) for detailed instructions.

### 💻 CLI (Command Line)

Traditional terminal interface for advanced users:

```bash
python src/main.py
```

See [QUICKSTART.md](QUICKSTART.md) for CLI usage.

## Architecture

```
┌─────────────┐
│   CLI UI    │  User enters prompt
└──────┬──────┘
       │
┌──────▼──────┐
│  LLM Planner│  Converts prompt → structured JSON plan
└──────┬──────┘
       │
┌──────▼──────┐
│  Validator  │  Checks allowlist, safety rules
└──────┬──────┘
       │
┌──────▼──────┐
│ Confirmation│  Shows plan, asks user approval
└──────┬──────┘
       │
┌──────▼──────┐
│  Executor   │  Runs actions using pywinauto/pyautogui
└──────┬──────┘
       │
┌──────▼──────┐
│   Logger    │  Audit log to SQLite
└─────────────┘
```

## MVP Features (Week 1)

- ✅ Text prompt input via CLI
- ✅ GPT-4 converts prompt to structured action plan
- ✅ Core actions: `open_folder`, `find_file`, `send_email`
- ✅ Confirmation dialog before execution
- ✅ Action logging to SQLite database
- ✅ Allowlist for safe paths/applications

## Tech Stack

- **Language:** Python 3.10+
- **LLM:** OpenAI GPT-4o-mini (configurable)
- **GUI Automation:** pywinauto, pyautogui
- **Email:** smtplib (Gmail/Outlook support)
- **Logging:** SQLite3
- **Configuration:** python-dotenv

## Project Structure

```
desktop-automation-agent/
├── README.md
├── ROADMAP.md
├── requirements.txt
├── .env.example
├── config/
│   ├── allowlist.json        # Allowed paths and applications
│   └── action_schema.json    # Supported action definitions
├── src/
│   ├── main.py              # CLI entry point
│   ├── planner.py           # LLM integration & prompt engineering
│   ├── validator.py         # Safety checks & allowlist enforcement
│   ├── executor.py          # Action execution engine
│   ├── actions/             # Individual action handlers
│   │   ├── __init__.py
│   │   ├── file_actions.py
│   │   ├── app_actions.py
│   │   └── email_actions.py
│   ├── logger.py            # Audit logging
│   └── utils.py             # Helpers
├── logs/
│   └── audit.db            # SQLite audit log (auto-created)
└── tests/
    └── test_actions.py
```

## Installation

### 1. Clone & Setup

```bash
cd desktop-automation-agent
python -m venv venv
venv\Scripts\activate  # On Windows
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and add your OpenAI API key:

```bash
cp .env.example .env
```

Edit `.env`:
```
OPENAI_API_KEY=your_api_key_here
MODEL_NAME=gpt-4o-mini
```

### 3. Configure Allowlist

Edit `config/allowlist.json` to specify which folders/apps the agent can access:

```json
{
  "allowed_folders": [
    "C:\\Users\\YourName\\Downloads",
    "C:\\Users\\YourName\\Desktop",
    "C:\\Users\\YourName\\Documents"
  ],
  "allowed_apps": [
    "notepad.exe",
    "calc.exe"
  ]
}
```

## Usage

### Basic Usage

```bash
python src/main.py
```

Then enter prompts:
```
> Open my Downloads folder
> Find the latest PDF in Documents
> Create a file on Desktop called todo.txt
```

### With Confirmation

By default, the agent will show you the planned actions and ask for confirmation:

```
Prompt: Open Downloads and find latest PDF

Planned Actions:
1. open_folder: C:\Users\You\Downloads
2. find_file: pattern=*.pdf, latest=true

Approve? [Y/n]:
```

### Dry Run Mode

Preview actions without executing:

```bash
python src/main.py --dry-run
```

## Safety Features

1. **Allowlist Enforcement:** Only access pre-approved folders and apps
2. **User Confirmation:** Review all actions before execution
3. **Audit Logging:** Every action logged with timestamp and result
4. **No Admin by Default:** Runs with user privileges only
5. **Action Limits:** Rate limiting on destructive operations

## Action Schema

Current supported actions (MVP):

| Action | Description | Args | Risk Level |
|--------|-------------|------|------------|
| `open_folder` | Opens folder in Explorer | `path` | 🟢 Low |
| `find_file` | Searches for files | `path`, `pattern`, `latest` | 🟢 Low |
| `open_file` | Opens file with default app | `path` | 🟡 Medium |
| `send_email` | Sends email via SMTP | `to`, `subject`, `body`, `attachments` | 🔴 High |
| `create_file` | Creates new text file | `path`, `content` | 🟡 Medium |

## Configuration

### Model Selection

Edit `.env` to change the LLM:

```
# Use GPT-4o-mini (faster, cheaper)
MODEL_NAME=gpt-4o-mini

# Use GPT-4 (more capable)
MODEL_NAME=gpt-4o
```

### Confirmation Levels

Edit `config/allowlist.json`:

```json
{
  "confirmation_mode": "always",  // always | selective | never
  "auto_approve_low_risk": false
}
```

## Logging & Audit

All actions are logged to `logs/audit.db`. View logs:

```bash
python src/main.py --view-logs
```

Or query directly:

```bash
sqlite3 logs/audit.db "SELECT * FROM actions ORDER BY timestamp DESC LIMIT 10;"
```

## Troubleshooting

### "Permission Denied" Errors
Check that the folder is in `config/allowlist.json`

### LLM Not Responding
Verify your OpenAI API key in `.env`

### Actions Failing
Check logs: `python src/main.py --view-logs --tail 5`

## Development

### Running Tests

```bash
pytest tests/
```

### Adding New Actions

1. Create handler in `src/actions/`
2. Add schema to `config/action_schema.json`
3. Register in `src/executor.py`
4. Add tests

## Security Considerations

- Store `.env` file securely (never commit to git)
- Review allowlist regularly
- Audit logs periodically for unexpected actions
- Use app-specific passwords for email (not main password)
- Consider running in a VM for high-risk experiments

## Roadmap

See [ROADMAP.md](ROADMAP.md) for planned features and future development.

## Contributing

This is a personal project MVP. Future: Add contribution guidelines.

## License

MIT License (or specify your preferred license)

## Disclaimer

This tool can perform actions on your computer. Use responsibly. Always review planned actions before approval. Start with allowlist restrictions and expand carefully.

---

**Status:** MVP - Week 1
**Last Updated:** 2025-11-11
