# Quick Start Guide

Get your Desktop Automation Agent running in 5 minutes!

## Step 1: Install Dependencies

```bash
cd desktop-automation-agent
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Step 2: Configure Environment

1. Copy the example environment file:
```bash
copy .env.example .env
```

2. Edit `.env` and add your OpenAI API key:
```
OPENAI_API_KEY=sk-your-api-key-here
```

3. (Optional) Configure email settings if you want to use `send_email`:
```
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_specific_password
```

For Gmail, create an app-specific password:
1. Go to Google Account → Security → 2-Step Verification
2. Scroll to "App passwords"
3. Generate a new app password for "Mail"
4. Use that password in `.env`

## Step 3: Configure Allowlist

Edit `config/allowlist.json` to specify which folders the agent can access:

```json
{
  "allowed_folders": [
    "C:\\Users\\YourName\\Downloads",
    "C:\\Users\\YourName\\Desktop",
    "C:\\Users\\YourName\\Documents"
  ]
}
```

Replace `YourName` with your actual Windows username, or leave `%USERNAME%` and it will auto-expand.

## Step 4: Run the Agent

```bash
python src/main.py
```

## Step 5: Try Some Commands

Once the CLI starts, try these example prompts:

### Basic File Operations
```
> Open my Downloads folder
> Find the latest PDF in Documents
> List files in Desktop
```

### File Creation
```
> Create a file on Desktop called todo.txt with content "Buy milk"
> Create a file in Documents called notes.txt with "Meeting at 3pm"
```

### Advanced
```
> Find the 3 largest files in Downloads
> Open the latest PDF from Documents
```

## Testing Without Executing

Run in dry-run mode to preview actions:

```bash
python src/main.py --dry-run
```

## View Logs

See what the agent has done:

```bash
python src/main.py --view-logs
```

## Common Issues

### "OpenAI API key not found"
- Make sure you created `.env` file (not `.env.example`)
- Check that `OPENAI_API_KEY` is set correctly

### "Path not in allowlist"
- Edit `config/allowlist.json` to add the folder
- Make sure to use Windows path format: `C:\\Users\\...`

### "Permission denied"
- Check that the folder exists and you have access rights
- Try running as administrator if needed (though not recommended)

### Email not working
- Verify `EMAIL_ADDRESS` and `EMAIL_PASSWORD` in `.env`
- For Gmail, use an app-specific password, not your regular password
- Check that SMTP settings are correct

## Safety Tips

1. **Start with read-only commands** - Test with `open_folder` and `find_file` first
2. **Use dry-run mode** - Preview actions before executing: `--dry-run`
3. **Check the plan** - Always review planned actions before approving
4. **Expand allowlist gradually** - Only add folders you trust
5. **Review logs** - Periodically check `--view-logs` for unexpected actions

## Next Steps

- Read [README.md](README.md) for full documentation
- Check [ROADMAP.md](ROADMAP.md) for upcoming features
- Customize `config/allowlist.json` for your needs
- Try more complex multi-step prompts

## Need Help?

- Run `help` inside the CLI
- Check the logs: `python src/main.py --view-logs`
- Review configuration files in `config/`

Happy automating!
