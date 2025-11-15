# Administrator Privileges Setup

## Why Admin Rights are Required

The Desktop Automation Agent requires administrator privileges to perform system-level operations:

- **Windows Firewall**: Enable/disable firewall, manage firewall rules
- **Windows Defender**: Run scans, manage threat protection
- **Bluetooth Settings**: Turn Bluetooth on/off, manage devices
- **Network Settings**: Modify WiFi, network adapters
- **System Settings**: Change power settings, display settings
- **Application Installation**: Install/uninstall applications

## Running with Administrator Privileges

### Method 1: Use the Admin Launcher (Recommended)

We've created convenient launcher scripts that handle admin elevation automatically:

1. **SETUP_AND_RUN.bat** - First-time setup and run
   - Checks environment
   - Verifies admin status
   - Launches application

2. **RUN_AS_ADMIN.bat** - Quick launch
   - Launches UI with admin privileges

**To use:**
- Right-click `SETUP_AND_RUN.bat` or `RUN_AS_ADMIN.bat`
- Select "Run as Administrator"
- Click "Yes" on UAC prompt

### Method 2: Manual Launch

If you prefer to launch manually:

```bash
# Open PowerShell as Administrator, then:
cd path\to\desktop-automation-agent\ui
npm start
```

## Admin Status Indicator

When running with admin privileges, you'll see:
- Window title: `Desktop Automation Agent [ADMINISTRATOR]`
- Console log: `[ADMIN] ✓ Running with Administrator privileges`

When running WITHOUT admin privileges:
- Window title: `Desktop Automation Agent`
- Console log: `[ADMIN] ⚠ Running WITHOUT Administrator privileges`
- Warning: Some operations may fail

## Automatic Admin Elevation

The application includes intelligent admin elevation:

1. **Automatic Detection**: Detects operations that need admin rights
   - PowerShell scripts with firewall/defender keywords
   - System settings modifications
   - Service management

2. **Dynamic Elevation**: Prompts for admin when needed
   - Shows UAC dialog for specific operations
   - Executes command with elevated privileges
   - Returns results to main application

3. **Clear Feedback**: Always shows what's happening
   ```
   [POWERSHELL] ⚠ Admin privileges required but not available
   [POWERSHELL] Attempting to execute with elevation...
   [POWERSHELL] ✓ Output (admin): ...
   ```

## Security Considerations

- **UAC Prompts**: You'll see UAC prompts for admin operations
- **Action Validation**: All actions are validated before execution
- **Audit Logging**: All operations are logged with timestamps
- **User Confirmation**: Complex operations require user approval

## Troubleshooting

### "Access Denied" Errors

If you see access denied errors:
1. Verify you're running as Administrator
2. Check UAC settings (should be enabled)
3. Restart the application as Administrator

### PowerShell Execution Policy

If PowerShell scripts fail:
```powershell
# Run as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Application Won't Start as Admin

If the batch files don't work:
1. Make sure you RIGHT-CLICK and select "Run as Administrator"
2. Don't double-click the .bat files
3. Alternatively, use PowerShell as Administrator:
   ```powershell
   cd ui
   npm start
   ```

## Best Practices

1. **Always run as Administrator** for full functionality
2. **Review actions** before approving them
3. **Check logs** if operations fail
4. **Keep UAC enabled** for security
5. **Use launcher scripts** for convenience

## For Developers

The admin elevation system is implemented in:
- `src/utils/admin_elevation.py` - Core elevation utilities
- `src/api_wrapper.py` - Admin status checking
- `src/actions/code_executor.py` - Auto-elevation for PowerShell
- `ui/main.js` - Admin status in Electron

Example usage in code:
```python
from utils.admin_elevation import is_admin, AdminElevation

# Check if running as admin
if is_admin():
    print("Running with admin privileges")

# Get detailed status
status = AdminElevation.get_admin_status()

# Run PowerShell with admin
success, stdout, stderr = AdminElevation.run_powershell_as_admin(
    "Set-NetFirewallProfile -Profile Domain -Enabled False"
)
```
