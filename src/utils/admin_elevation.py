"""
Windows Administrator Privilege Management
Professional elevation system for desktop automation
"""

import ctypes
import sys
import os
import subprocess
from typing import Optional, Tuple


class AdminElevation:
    """
    Professional Windows Administrator Privilege Manager
    Handles elevation, checks, and re-launching with admin rights
    """

    @staticmethod
    def is_admin() -> bool:
        """
        Check if the current process is running with administrator privileges

        Returns:
            True if running as admin, False otherwise
        """
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False

    @staticmethod
    def get_admin_status() -> dict:
        """
        Get detailed administrator status information

        Returns:
            Dictionary with admin status details
        """
        is_admin = AdminElevation.is_admin()

        return {
            'is_admin': is_admin,
            'message': 'Running with Administrator privileges' if is_admin else 'Running without Administrator privileges',
            'recommendation': None if is_admin else 'Please run as Administrator for full functionality'
        }

    @staticmethod
    def request_elevation() -> bool:
        """
        Request UAC elevation by re-launching the current script with admin rights
        IMPORTANT: This will terminate the current process if successful

        Returns:
            True if elevation was requested (process will exit), False if failed
        """
        try:
            # Get the path to the Python executable
            python_exe = sys.executable

            # Get the current script path
            script = sys.argv[0]

            # Get all command-line arguments
            params = ' '.join([f'"{arg}"' for arg in sys.argv[1:]])

            # Request elevation using ShellExecute with 'runas' verb
            result = ctypes.windll.shell32.ShellExecuteW(
                None,                   # hwnd
                "runas",                # lpOperation - request admin
                python_exe,             # lpFile - Python executable
                f'"{script}" {params}', # lpParameters - script + args
                None,                   # lpDirectory
                1                       # nShowCmd - SW_NORMAL
            )

            # If result > 32, the elevation was successful
            if result > 32:
                # Exit the current (non-elevated) process
                sys.exit(0)
                return True
            else:
                print(f"[ADMIN] Elevation failed with code: {result}", file=sys.stderr)
                return False

        except Exception as e:
            print(f"[ADMIN] Failed to request elevation: {e}", file=sys.stderr)
            return False

    @staticmethod
    def run_as_admin(command: str, args: str = "", wait: bool = False) -> Optional[subprocess.Popen]:
        """
        Run a specific command with administrator privileges

        Args:
            command: Command or executable to run
            args: Command-line arguments
            wait: If True, wait for process to complete

        Returns:
            Popen object if successful, None otherwise
        """
        try:
            # Use PowerShell Start-Process with -Verb RunAs for elevation
            ps_command = f'Start-Process -FilePath "{command}"'

            if args:
                ps_command += f' -ArgumentList "{args}"'

            ps_command += ' -Verb RunAs'

            if wait:
                ps_command += ' -Wait'
            else:
                ps_command += ' -WindowStyle Hidden'

            # Execute PowerShell command
            process = subprocess.Popen(
                ['powershell.exe', '-Command', ps_command],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            if wait:
                process.wait()

            return process

        except Exception as e:
            print(f"[ADMIN] Failed to run command as admin: {e}", file=sys.stderr)
            return None

    @staticmethod
    def ensure_admin(auto_elevate: bool = False) -> Tuple[bool, str]:
        """
        Ensure the application is running with administrator privileges

        Args:
            auto_elevate: If True, automatically request elevation if not admin

        Returns:
            Tuple of (is_admin, message)
        """
        if AdminElevation.is_admin():
            return True, "Running with Administrator privileges"

        message = "Not running as Administrator"

        if auto_elevate:
            print("[ADMIN] Requesting administrator elevation...", file=sys.stderr)
            if AdminElevation.request_elevation():
                # This line won't be reached if elevation succeeds (process exits)
                return False, "Elevation requested - process will restart"
            else:
                return False, f"{message}. Elevation failed - please run as Administrator manually"
        else:
            return False, f"{message}. Some operations may fail. Run as Administrator for full functionality"

    @staticmethod
    def run_powershell_as_admin(script: str, wait: bool = True) -> Tuple[bool, str, str]:
        """
        Run a PowerShell script with administrator privileges

        Args:
            script: PowerShell script to execute
            wait: If True, wait for completion and return output

        Returns:
            Tuple of (success, stdout, stderr)
        """
        try:
            # Create a temporary script file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.ps1', delete=False) as f:
                f.write(script)
                script_path = f.name

            try:
                # Run PowerShell script with elevation
                ps_command = f'Start-Process powershell.exe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File \'{script_path}\'" -Verb RunAs'

                if wait:
                    ps_command += ' -Wait -WindowStyle Hidden'

                process = subprocess.Popen(
                    ['powershell.exe', '-Command', ps_command],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )

                if wait:
                    stdout, stderr = process.communicate()
                    return (
                        process.returncode == 0,
                        stdout.decode('utf-8', errors='ignore'),
                        stderr.decode('utf-8', errors='ignore')
                    )
                else:
                    return True, "", ""

            finally:
                # Clean up temp file
                try:
                    os.unlink(script_path)
                except:
                    pass

        except Exception as e:
            return False, "", str(e)


# Convenience function for quick admin checks
def is_admin() -> bool:
    """Quick check if running as administrator"""
    return AdminElevation.is_admin()


def require_admin(auto_elevate: bool = False) -> bool:
    """
    Require admin privileges or exit

    Args:
        auto_elevate: If True, try to elevate automatically

    Returns:
        True if admin, exits or returns False otherwise
    """
    is_admin_status, message = AdminElevation.ensure_admin(auto_elevate)

    if not is_admin_status:
        print(f"[ADMIN] {message}", file=sys.stderr)
        if not auto_elevate:
            print("[ADMIN] Please run this application as Administrator", file=sys.stderr)
            print("[ADMIN] Right-click and select 'Run as Administrator'", file=sys.stderr)

    return is_admin_status
