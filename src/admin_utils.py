"""
Admin Privilege Management - Checks and requests admin elevation
"""

import sys
import ctypes
import os


def is_admin():
    """
    Check if the current process has administrator privileges

    Returns:
        bool: True if running as admin, False otherwise
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def request_admin_elevation():
    """
    Restart the current script with administrator privileges

    This will:
    1. Show UAC prompt to user
    2. Restart the script with admin rights if approved
    3. Exit the current process

    Returns:
        None (exits process if elevation succeeds)

    Raises:
        Exception: If elevation fails or is denied
    """
    if is_admin():
        # Already running as admin
        return

    try:
        # Get the current script path and arguments
        script = os.path.abspath(sys.argv[0])
        params = ' '.join([f'"{arg}"' if ' ' in arg else arg for arg in sys.argv[1:]])

        # Request elevation via ShellExecute with 'runas' verb
        # This triggers the UAC prompt
        ret = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",  # Verb for running as administrator
            sys.executable,  # Python executable
            f'"{script}" {params}',  # Script and arguments
            None,
            1  # SW_SHOWNORMAL
        )

        if ret > 32:  # Success
            # Exit current process - the elevated process will take over
            sys.exit(0)
        else:
            # Elevation failed
            raise Exception(f"Failed to elevate privileges (error code: {ret})")

    except Exception as e:
        raise Exception(f"Admin elevation failed: {str(e)}")


def prompt_for_admin(interactive=True):
    """
    Prompt user for admin privileges and handle elevation

    Args:
        interactive: If True, asks user before elevating. If False, elevates automatically.

    Returns:
        bool: True if running with admin (either already or after elevation), False if user declined
    """
    if is_admin():
        return True

    print("\n" + "="*70)
    print("  ADMIN PRIVILEGES REQUIRED")
    print("="*70)
    print()
    print("Some operations require administrator privileges:")
    print("  • Bluetooth control (turn on/off)")
    print("  • Windows Firewall management")
    print("  • System settings modifications")
    print()
    print("The agent can run without admin, but these features will be limited.")
    print()

    if interactive:
        response = input("Request admin privileges now? (y/n): ").strip().lower()

        if response in ['y', 'yes']:
            try:
                print("\nRequesting admin elevation...")
                print("Please approve the UAC prompt to continue with full functionality.\n")
                request_admin_elevation()
                # If we get here, elevation failed (normally it exits)
                return False
            except Exception as e:
                print(f"\n[WARNING] {str(e)}")
                print("Continuing without admin privileges. Some features will be limited.\n")
                return False
        else:
            print("\nContinuing without admin privileges. Some features will be limited.\n")
            return False
    else:
        # Non-interactive mode - just try to elevate
        try:
            request_admin_elevation()
            return True
        except:
            return False
