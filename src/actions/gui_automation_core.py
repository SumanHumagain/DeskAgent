"""
Professional GUI Automation Core using pywinauto
Systematic, accurate automation for ALL Windows operations
"""

import sys
import time
import platform
from typing import Optional, Dict, List, Any
from pywinauto import Application, Desktop
from pywinauto.findwindows import ElementNotFoundError
from pywinauto.timings import TimeoutError as PywinautoTimeoutError


class WindowsGUIAutomation:
    """
    Robust GUI automation using pywinauto
    Works systematically across Windows 10/11
    """

    def __init__(self):
        """Initialize GUI automation with OS detection"""
        self.os_version = self._detect_windows_version()
        self.desktop = Desktop(backend="uia")  # Use UI Automation backend
        print(f"[GUI CORE] Initialized for {self.os_version}", file=sys.stderr)

    def _detect_windows_version(self) -> str:
        """Detect Windows version for adaptive behavior"""
        version = platform.version()
        release = platform.release()

        if "11" in release or "22000" in version:
            return "Windows 11"
        elif "10" in release:
            return "Windows 10"
        else:
            return f"Windows {release}"

    def find_window(self, search_terms: List[str], timeout: int = 5, debug: bool = True) -> Optional[Any]:
        """
        Find a window by searching for titles containing search terms
        WITH INTELLIGENT DEBUGGING AND TASKBAR EXCLUSION

        Args:
            search_terms: List of strings to search for in window title
            timeout: Maximum time to wait for window
            debug: If True, logs all available windows when search fails

        Returns:
            Window object if found, None otherwise
        """
        print(f"[GUI CORE] Searching for window with terms: {search_terms}", file=sys.stderr)

        start_time = time.time()
        all_window_titles = set()  # Collect all seen window titles for debugging

        # Windows to exclude from search (system windows that shouldn't be interacted with)
        excluded_windows = ["Taskbar", "Program Manager", "Start", ""]

        while time.time() - start_time < timeout:
            try:
                windows = self.desktop.windows()

                # First pass: Look for exact matches (excluding system windows)
                for window in windows:
                    try:
                        title = window.window_text()

                        # Skip empty titles
                        if not title or not title.strip():
                            continue

                        # Skip excluded system windows
                        if title in excluded_windows:
                            continue

                        # Collect for debugging
                        if title not in all_window_titles:
                            all_window_titles.add(title)

                        # Check if any search term matches the title
                        for term in search_terms:
                            # Empty term matches any window (but not excluded ones)
                            if not term:
                                if title not in excluded_windows:
                                    print(f"[GUI CORE] Found window (fallback): '{title}'", file=sys.stderr)
                                    return window
                            # Exact or partial match
                            elif term.lower() in title.lower():
                                print(f"[GUI CORE] Found window: '{title}' (matched '{term}')", file=sys.stderr)
                                return window

                    except Exception:
                        continue

            except Exception as e:
                print(f"[GUI CORE] Search error: {e}", file=sys.stderr)

            time.sleep(0.5)

        # Search failed - provide helpful debugging
        print(f"[GUI CORE] Window not found after {timeout}s", file=sys.stderr)

        if debug and all_window_titles:
            print(f"[GUI CORE] DEBUG: Available windows found during search:", file=sys.stderr)
            non_system_windows = [t for t in all_window_titles if t not in excluded_windows]
            for title in sorted(non_system_windows)[:20]:  # Show first 20
                print(f"[GUI CORE]   - '{title}'", file=sys.stderr)

        return None

    def find_control(self, window: Any, control_type: str = None,
                    name: str = None, auto_id: str = None,
                    class_name: str = None, partial_match: bool = True) -> Optional[Any]:
        """
        Find a control within a window using multiple strategies

        Args:
            window: Parent window object
            control_type: Type of control (Button, Edit, CheckBox, etc.)
            name: Name or text of the control
            auto_id: Automation ID
            class_name: Class name
            partial_match: Allow partial name matches

        Returns:
            Control object if found, None otherwise
        """
        try:
            # Strategy 1: Find by name/text
            if name:
                try:
                    if partial_match:
                        # Find controls containing the name
                        controls = window.descendants(control_type=control_type)
                        for ctrl in controls:
                            try:
                                ctrl_text = ctrl.window_text()
                                if name.lower() in ctrl_text.lower():
                                    print(f"[GUI CORE] Found control: '{ctrl_text}'", file=sys.stderr)
                                    return ctrl
                            except:
                                continue
                    else:
                        # Exact match
                        return window.child_window(title=name, control_type=control_type)
                except:
                    pass

            # Strategy 2: Find by automation ID
            if auto_id:
                try:
                    return window.child_window(auto_id=auto_id, control_type=control_type)
                except:
                    pass

            # Strategy 3: Find by class name
            if class_name:
                try:
                    return window.child_window(class_name=class_name, control_type=control_type)
                except:
                    pass

            print(f"[GUI CORE] Control not found: type={control_type}, name={name}", file=sys.stderr)
            return None

        except Exception as e:
            print(f"[GUI CORE] Error finding control: {e}", file=sys.stderr)
            return None

    def click_control(self, control: Any) -> bool:
        """
        Click a control with retry logic

        Args:
            control: Control to click

        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure control is visible and enabled
            if not control.is_visible() or not control.is_enabled():
                print(f"[GUI CORE] Control not clickable: visible={control.is_visible()}, enabled={control.is_enabled()}", file=sys.stderr)
                return False

            # Try to set focus first
            try:
                control.set_focus()
                time.sleep(0.2)
            except:
                pass

            # Click the control
            control.click_input()
            time.sleep(0.3)

            print(f"[GUI CORE] Clicked: {control.window_text()}", file=sys.stderr)
            return True

        except Exception as e:
            print(f"[GUI CORE] Click failed: {e}", file=sys.stderr)
            return False

    def set_toggle(self, control: Any, state: bool) -> bool:
        """
        Set a toggle/checkbox state

        Args:
            control: Toggle control
            state: True for on/checked, False for off/unchecked

        Returns:
            True if successful, False otherwise
        """
        try:
            current_state = control.get_toggle_state()

            if (state and current_state == 0) or (not state and current_state == 1):
                # Need to toggle
                control.click_input()
                time.sleep(0.3)

            print(f"[GUI CORE] Set toggle to: {state}", file=sys.stderr)
            return True

        except Exception as e:
            print(f"[GUI CORE] Toggle failed: {e}", file=sys.stderr)
            # Fallback: just click it
            try:
                control.click_input()
                return True
            except:
                return False

    def open_settings_page(self, settings_uri: str) -> Optional[Any]:
        """
        Open a Windows Settings page using ms-settings: URI

        Args:
            settings_uri: Settings URI (e.g., "ms-settings:network-wifi")

        Returns:
            Settings window if found, None otherwise
        """
        import subprocess

        try:
            print(f"[GUI CORE] Opening settings: {settings_uri}", file=sys.stderr)
            subprocess.Popen(f'start {settings_uri}', shell=True)

            # Wait for Settings window to appear
            time.sleep(1.5)

            # Find the Settings window
            settings_window = self.find_window(["Settings"], timeout=5)

            if settings_window:
                print(f"[GUI CORE] Settings window opened", file=sys.stderr)
                return settings_window
            else:
                print(f"[GUI CORE] Settings window not found", file=sys.stderr)
                return None

        except Exception as e:
            print(f"[GUI CORE] Failed to open settings: {e}", file=sys.stderr)
            return None

    def navigate_and_click(self, window: Any, navigation_path: List[str]) -> bool:
        """
        Navigate through UI by clicking elements in sequence

        Args:
            window: Starting window
            navigation_path: List of element names to click in order

        Returns:
            True if all elements clicked successfully, False otherwise
        """
        current_window = window

        for element_name in navigation_path:
            print(f"[GUI CORE] Looking for: {element_name}", file=sys.stderr)

            # Find and click the element
            control = self.find_control(current_window, name=element_name)

            if not control:
                # Try as button specifically
                control = self.find_control(current_window, control_type="Button", name=element_name)

            if not control:
                # Try as text/hyperlink
                control = self.find_control(current_window, control_type="Hyperlink", name=element_name)

            if control:
                if self.click_control(control):
                    time.sleep(0.5)  # Wait for UI to update
                    current_window = window  # Continue from same window
                else:
                    print(f"[GUI CORE] Failed to click: {element_name}", file=sys.stderr)
                    return False
            else:
                print(f"[GUI CORE] Element not found: {element_name}", file=sys.stderr)
                return False

        return True

    def get_window_controls_tree(self, window: Any, max_depth: int = 3) -> Dict:
        """
        Get a tree of all controls in a window (for debugging)

        Args:
            window: Window to inspect
            max_depth: Maximum depth to traverse

        Returns:
            Dictionary representing the control tree
        """
        def get_control_info(ctrl, depth=0):
            if depth > max_depth:
                return None

            try:
                info = {
                    "type": ctrl.element_info.control_type,
                    "name": ctrl.window_text(),
                    "auto_id": ctrl.element_info.automation_id,
                    "class": ctrl.element_info.class_name,
                    "visible": ctrl.is_visible(),
                    "enabled": ctrl.is_enabled()
                }

                # Get children
                children = []
                for child in ctrl.children():
                    child_info = get_control_info(child, depth + 1)
                    if child_info:
                        children.append(child_info)

                if children:
                    info["children"] = children

                return info
            except:
                return None

        return get_control_info(window)
