"""
Application control action handlers
"""

import subprocess
import psutil
import os
import json
from pathlib import Path
from typing import Optional, List, Dict


class AppActions:
    """Handles application launching and control with smart executable detection"""

    def __init__(self):
        """Initialize with cache for found executables"""
        self.cache_file = Path(__file__).parent.parent.parent / 'config' / 'app_cache.json'
        self.app_cache = self._load_cache()

    def _load_cache(self) -> dict:
        """Load cached application paths"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}

    def _save_cache(self):
        """Save application paths to cache"""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_file, 'w') as f:
            json.dump(self.app_cache, f, indent=2)

    def _find_executable(self, app_name: str) -> Optional[str]:
        """
        Dynamically search for an application executable

        Args:
            app_name: Application name (e.g., "postman", "slack")

        Returns:
            Full path to executable if found, None otherwise
        """
        import sys

        # Check cache first
        cache_key = app_name.lower()
        if cache_key in self.app_cache:
            cached_path = self.app_cache[cache_key]
            if os.path.exists(cached_path):
                print(f"[SMART LAUNCH] Found {app_name} in cache: {cached_path}", file=sys.stderr)
                return cached_path

        print(f"[SMART LAUNCH] Searching for {app_name}...", file=sys.stderr)

        # Normalize app name
        if not app_name.lower().endswith('.exe'):
            exe_name = f"{app_name}.exe"
        else:
            exe_name = app_name

        # Common search locations
        search_paths = [
            os.path.join(os.environ.get('LOCALAPPDATA', ''), app_name.title()),
            os.path.join(os.environ.get('LOCALAPPDATA', ''), app_name),
            os.path.join(os.environ.get('PROGRAMFILES', ''), app_name.title()),
            os.path.join(os.environ.get('PROGRAMFILES', ''), app_name),
            os.path.join(os.environ.get('PROGRAMFILES(X86)', ''), app_name.title()),
            os.path.join(os.environ.get('PROGRAMFILES(X86)', ''), app_name),
        ]

        # Search in common locations
        for search_path in search_paths:
            if os.path.exists(search_path):
                for root, dirs, files in os.walk(search_path):
                    for file in files:
                        if file.lower() == exe_name.lower():
                            full_path = os.path.join(root, file)
                            print(f"[SMART LAUNCH] Found executable: {full_path}", file=sys.stderr)
                            # Cache the result
                            self.app_cache[cache_key] = full_path
                            self._save_cache()
                            return full_path
                    # Only search top level to avoid slow deep searches
                    break

        print(f"[SMART LAUNCH] Executable not found for {app_name}", file=sys.stderr)
        return None

    # No hardcoded mappings - GPT will dynamically determine the correct command

    def open_app(self, app_name: str, args: Optional[List[str]] = None) -> str:
        """
        Launch an application

        Args:
            app_name: Application name or path
            args: Optional command-line arguments

        Returns:
            Success message
        """
        # Normalize app name
        app_name_lower = app_name.lower()

        # Check if it's a known app
        if app_name_lower in self.KNOWN_APPS:
            executable = self.KNOWN_APPS[app_name_lower]
        elif app_name.endswith('.exe'):
            executable = app_name
        else:
            executable = f"{app_name}.exe"

        # Build command
        cmd = [executable]
        if args:
            cmd.extend(args)

        # Launch the application
        process = subprocess.Popen(cmd)

        return f"Launched {app_name} (PID: {process.pid})"

    def is_app_running(self, app_name: str) -> bool:
        """
        Check if an application is currently running

        Args:
            app_name: Application name (e.g., 'notepad.exe')

        Returns:
            True if running, False otherwise
        """
        app_name = app_name.lower()
        if not app_name.endswith('.exe'):
            app_name = f"{app_name}.exe"

        for process in psutil.process_iter(['name']):
            try:
                if process.info['name'].lower() == app_name:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return False

    def list_running_apps(self) -> List[Dict]:
        """
        List all running applications

        Returns:
            List of dicts with app info
        """
        apps = []

        for process in psutil.process_iter(['pid', 'name', 'username']):
            try:
                info = process.info
                apps.append({
                    'pid': info['pid'],
                    'name': info['name'],
                    'user': info.get('username', 'unknown')
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return apps

    def launch_app(self, command: str, args: Optional[str] = None) -> str:
        """
        Launch any Windows application or system utility with SMART DETECTION
        Automatically searches for executables if command not found in PATH

        Args:
            command: Windows command to execute (e.g., 'control', 'taskmgr', 'notepad.exe', 'postman')
            args: Optional command-line arguments

        Returns:
            Success message with actual command executed
        """
        import sys
        import time

        # Build the full command string
        if args:
            full_command = f"{command} {args}"
        else:
            full_command = command

        # Log what we're executing
        print(f"[LAUNCH] Attempting: {full_command}", file=sys.stderr)

        # Try launching directly first (NON-BLOCKING)
        try:
            # Launch without waiting - Windows DETACHED_PROCESS flag
            DETACHED_PROCESS = 0x00000008
            CREATE_NEW_PROCESS_GROUP = 0x00000200

            process = subprocess.Popen(
                full_command,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
            )

            # Quick check if it failed immediately (non-blocking)
            time.sleep(0.2)
            poll_result = process.poll()

            if poll_result is not None and poll_result != 0:
                # Process ended with error - check stderr
                try:
                    stderr = process.stderr.read().decode('utf-8', errors='ignore')
                except:
                    stderr = ""

                # Check if it's a "not recognized" error (command not found)
                if "not recognized" in stderr or "not found" in stderr or poll_result != 0:
                    print(f"[LAUNCH] Command not found, trying smart detection...", file=sys.stderr)
                    # SMART DETECTION: Try to find the executable
                    found_path = self._find_executable(command)

                    if found_path:
                        # Try launching with the found path (DETACHED)
                        print(f"[LAUNCH] Launching with found path: {found_path}", file=sys.stderr)
                        if args:
                            smart_command = f'"{found_path}" {args}'
                        else:
                            smart_command = f'"{found_path}"'

                        subprocess.Popen(
                            smart_command,
                            shell=True,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            stdin=subprocess.DEVNULL,
                            creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
                        )

                        return f"✓ Launched {command} (auto-detected at: {found_path})"
                    else:
                        raise Exception(f"Command '{command}' not found in PATH and could not auto-detect executable. Please install {command} or provide the full path.")

            print(f"[LAUNCH] Successfully launched: {full_command}", file=sys.stderr)
            return f"✓ Launched: {command}"

        except FileNotFoundError:
            # Command not found - try smart detection
            print(f"[LAUNCH] FileNotFoundError - trying smart detection...", file=sys.stderr)
            found_path = self._find_executable(command)

            if found_path:
                print(f"[LAUNCH] Launching with found path: {found_path}", file=sys.stderr)
                if args:
                    smart_command = f'"{found_path}" {args}'
                else:
                    smart_command = f'"{found_path}"'

                # Launch DETACHED (non-blocking)
                DETACHED_PROCESS = 0x00000008
                CREATE_NEW_PROCESS_GROUP = 0x00000200
                subprocess.Popen(
                    smart_command,
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                    creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
                )
                return f"✓ Launched {command} (auto-detected at: {found_path})"
            else:
                raise Exception(f"Could not find '{command}'. Please install it or provide the full path.")

        except Exception as e:
            # Last resort - try smart detection if not already tried
            if "auto-detect" not in str(e):
                print(f"[LAUNCH] Exception: {str(e)} - trying smart detection...", file=sys.stderr)
                found_path = self._find_executable(command)

                if found_path:
                    print(f"[LAUNCH] Launching with found path: {found_path}", file=sys.stderr)
                    if args:
                        smart_command = f'"{found_path}" {args}'
                    else:
                        smart_command = f'"{found_path}"'

                    # Launch DETACHED (non-blocking)
                    DETACHED_PROCESS = 0x00000008
                    CREATE_NEW_PROCESS_GROUP = 0x00000200
                    subprocess.Popen(
                        smart_command,
                        shell=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        stdin=subprocess.DEVNULL,
                        creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
                    )
                    return f"✓ Launched {command} (auto-detected at: {found_path})"

            # All methods failed
            raise Exception(f"Failed to launch '{command}': {str(e)}")
