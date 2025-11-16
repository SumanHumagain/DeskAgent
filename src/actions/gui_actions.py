"""
GUI automation using pywinauto - SYSTEMATIC & ACCURATE
Uses professional GUI automation core for ALL operations
"""

import sys
import time
import json
import subprocess
from typing import Dict, List, Optional
from pywinauto import Desktop, Application
from pywinauto.findwindows import ElementNotFoundError

# Import our professional GUI automation core
from actions.gui_automation_core import WindowsGUIAutomation


class GUIActions:
    """
    Handles GUI automation SYSTEMATICALLY using professional core
    Works accurately across ALL Windows operations
    """

    def __init__(self):
        self.desktop = Desktop(backend="uia")
        # Initialize professional GUI core
        self.gui_core = WindowsGUIAutomation()
        print(f"[GUI ACTIONS] Initialized with professional automation core", file=sys.stderr)

    def _find_window_fuzzy(self, search_terms: List[str], timeout: int = 5) -> Optional[object]:
        """Find window using fuzzy matching"""
        end_time = time.time() + timeout
        while time.time() < end_time:
            windows = self.desktop.windows()
            for window in windows:
                try:
                    title = window.window_text().lower()
                    if any(term.lower() in title for term in search_terms):
                        return window
                except:
                    continue
            time.sleep(0.5)
        return None

    def _find_control_fuzzy(self, parent, search_name: str, control_types: List[str] = None) -> Optional[object]:
        """Find control using fuzzy matching on multiple control types"""
        if control_types is None:
            control_types = ["Hyperlink", "Text", "Button", "MenuItem"]

        print(f"[GUI] Searching for '{search_name}' in control types: {control_types}", file=sys.stderr)

        # Manually enumerate descendants and search
        search_lower = search_name.lower()
        try:
            for child in parent.descendants():
                try:
                    text = child.window_text()
                    if not text:
                        continue

                    ctype = child.element_info.control_type

                    # Check if control type matches
                    if ctype not in control_types:
                        continue

                    # Check for exact or partial match
                    text_lower = text.lower()
                    if search_lower == text_lower:
                        print(f"[GUI] Found exact match: '{text}' ({ctype})", file=sys.stderr)
                        return child
                    elif search_lower in text_lower:
                        print(f"[GUI] Found fuzzy match: '{text}' ({ctype})", file=sys.stderr)
                        return child
                except:
                    continue
        except Exception as e:
            print(f"[GUI] Error during search: {e}", file=sys.stderr)

        # List available controls for debugging (only relevant ones)
        try:
            print(f"[GUI] Could not find '{search_name}'. Available controls with matching types:", file=sys.stderr)
            for child in parent.descendants():
                try:
                    text = child.window_text()
                    if not text:
                        continue
                    ctype = child.element_info.control_type
                    if ctype in control_types:
                        print(f"[GUI]   - '{text}' (type={ctype})", file=sys.stderr)
                except:
                    pass
        except:
            pass

        return None

    def navigate_control_panel_settings(self, ui_path: List[str], action: Dict) -> str:
        """
        Navigate through Control Panel or Settings UI with dynamic multi-strategy approach

        Args:
            ui_path: List of UI elements to navigate (e.g., ["Control Panel", "Mouse", "Pointer Options"])
            action: Action to perform (e.g., {"type": "slider", "name": "speed", "value": "slow"})

        Returns:
            Success message
        """
        try:
            print(f"[GUI] Navigating path: {ui_path}", file=sys.stderr)
            print(f"[GUI] Action: {action}", file=sys.stderr)

            # DYNAMIC APPROACH: Detect if this is a volume/speaker control request
            # Try multiple strategies in order of reliability
            is_volume_control = any(
                keyword in str(ui_path).lower() or keyword in str(action).lower()
                for keyword in ["volume", "sound", "speaker", "audio", "mute"]
            )

            if is_volume_control:
                print(f"[GUI] Detected volume control request - using multi-strategy approach", file=sys.stderr)
                return self._handle_volume_control_dynamic(action)

            # Step 1: Determine what to open based on ui_path[0]
            target_window = None

            if "Control Panel" in ui_path[0] or "control" in ui_path[0].lower():
                # Open Control Panel
                import subprocess
                subprocess.Popen("control", shell=True)
                print(f"[GUI] Waiting for Control Panel to open...", file=sys.stderr)
                time.sleep(3)
                target_window = self._find_window_fuzzy(["control panel", "settings", "all control panel items"])

            elif "Settings" in ui_path[0] or "settings" in ui_path[0].lower():
                # Open Windows Settings - try multiple possible URIs dynamically
                import subprocess

                # Try to open specific settings page if we can infer it
                settings_uri = "ms-settings:"
                if len(ui_path) > 1:
                    category = ui_path[1].lower()
                    if "sound" in category or "audio" in category:
                        settings_uri = "ms-settings:sound"
                    elif "display" in category:
                        settings_uri = "ms-settings:display"
                    elif "bluetooth" in category:
                        settings_uri = "ms-settings:bluetooth"

                subprocess.Popen(f"start {settings_uri}", shell=True)
                print(f"[GUI] Opening Settings with URI: {settings_uri}", file=sys.stderr)
                time.sleep(2)

                # Try multiple possible window titles dynamically
                target_window = self._find_window_fuzzy(["settings", "system settings", "windows settings", "sound", "system"])

            else:
                # For anything else (like "Speakers", "Network", etc.), try to find as system tray icon
                print(f"[GUI] Looking for '{ui_path[0]}' (could be system tray icon or window)...", file=sys.stderr)

                # First, try to find it as a system tray icon and click it
                # System tray is part of the taskbar
                taskbar = self._find_window_fuzzy(["taskbar"])
                if taskbar:
                    print(f"[GUI] Found taskbar, searching for '{ui_path[0]}' icon...", file=sys.stderr)
                    icon = self._find_control_fuzzy(taskbar, ui_path[0], ["Button"])
                    if icon:
                        print(f"[GUI] Found and clicking system tray icon: {ui_path[0]}", file=sys.stderr)
                        icon.click_input()
                        time.sleep(1)
                        # Now find the popup window that opened
                        target_window = self._find_window_fuzzy([ui_path[0], "volume", "slider"])
                    else:
                        print(f"[GUI] '{ui_path[0]}' not found in system tray, trying as window name...", file=sys.stderr)

                # If not found as system tray icon, try finding as a window
                if not target_window:
                    target_window = self._find_window_fuzzy([ui_path[0]])

            if not target_window:
                raise Exception(f"Could not find target window/icon: {ui_path[0]}")

            print(f"[GUI] Found window: {target_window.window_text()}", file=sys.stderr)

            # Step 3: Navigate to target (e.g., "Mouse", "File Explorer Options")
            # If ui_path has only 1 element, we're already at the target (e.g., system tray icon clicked)
            dialog = None
            if len(ui_path) > 1:
                target_name = ui_path[1]
                print(f"[GUI] Looking for: {target_name}", file=sys.stderr)

                # Find and click the target using fuzzy matching
                target_control = self._find_control_fuzzy(target_window, target_name)

                if not target_control:
                    raise Exception(f"Could not find '{target_name}' in Control Panel. Check debug logs for available controls.")

                print(f"[GUI] Clicking on: {target_control.window_text()}", file=sys.stderr)
                target_control.click_input()
                time.sleep(2)

                # Find the dialog/properties window that opened
                dialog = self._find_window_fuzzy(["properties", "options", ui_path[1]], timeout=3)

            # If ui_path has only 1 element, the target_window itself is what we work with
            if not dialog and len(ui_path) == 1:
                dialog = target_window

            # Step 4: Handle tabs if specified (e.g., "Pointer Options" tab, "View" tab)
            if len(ui_path) > 2:
                tab_name = ui_path[2]
                print(f"[GUI] Switching to tab: {tab_name}", file=sys.stderr)

                if dialog:
                    print(f"[GUI] Found dialog: {dialog.window_text()}", file=sys.stderr)

                    # Try to find the tab
                    tab_control = self._find_control_fuzzy(dialog, tab_name, ["TabItem"])

                    if tab_control:
                        print(f"[GUI] Switching to tab: {tab_control.window_text()}", file=sys.stderr)
                        tab_control.click_input()
                        time.sleep(0.5)
                    else:
                        print(f"[GUI] Warning: Could not find tab '{tab_name}'", file=sys.stderr)
                else:
                    print(f"[GUI] Warning: Could not find properties/options dialog", file=sys.stderr)

            # Step 5: Perform the action
            action_type = action.get("type")

            if action_type == "checkbox":
                checkbox_name = action.get("name")
                checkbox_value = action.get("value", True)

                print(f"[GUI] Setting checkbox '{checkbox_name}' to {checkbox_value}", file=sys.stderr)

                # Find checkbox using fuzzy matching
                parent = dialog if dialog else target_window
                checkbox = self._find_control_fuzzy(parent, checkbox_name, ["CheckBox"])

                if not checkbox:
                    raise Exception(f"Could not find checkbox '{checkbox_name}'")

                current_state = checkbox.get_toggle_state()
                target_state = 1 if checkbox_value else 0

                if current_state != target_state:
                    checkbox.click_input()
                    print(f"[GUI] Checkbox toggled", file=sys.stderr)
                else:
                    print(f"[GUI] Checkbox already in desired state", file=sys.stderr)

                # Click Apply/OK button
                apply_btn = self._find_control_fuzzy(parent, "Apply", ["Button"])
                if apply_btn:
                    apply_btn.click_input()
                    time.sleep(0.3)

                ok_btn = self._find_control_fuzzy(parent, "OK", ["Button"])
                if ok_btn:
                    ok_btn.click_input()

                return f"Successfully set '{checkbox_name}' to {checkbox_value}"

            elif action_type == "slider":
                slider_name = action.get("name", "")
                slider_value = action.get("value", "")

                print(f"[GUI] Adjusting slider '{slider_name}' to '{slider_value}'", file=sys.stderr)

                # Find slider - for generic names like "speed" or "motion", just use the first slider
                generic_slider_names = ["speed", "motion", "pointer", "rate", "slider", "volume", "brightness"]

                parent = dialog if dialog else target_window

                if slider_name.lower() in generic_slider_names:
                    print(f"[GUI] Generic slider name detected, finding first available slider", file=sys.stderr)
                    slider = None
                    try:
                        for child in parent.descendants():
                            try:
                                if child.element_info.control_type == "Slider":
                                    slider = child
                                    print(f"[GUI] Using slider: '{child.window_text()}'", file=sys.stderr)
                                    break
                            except:
                                continue
                    except:
                        pass
                else:
                    # Find slider using fuzzy matching
                    slider = self._find_control_fuzzy(parent, slider_name, ["Slider"])

                if not slider:
                    print(f"[GUI] Could not find slider '{slider_name}'", file=sys.stderr)
                    raise Exception(f"Could not find slider '{slider_name}'")

                # Adjust slider based on value
                if slider_value.lower() in ["slow", "slowest", "min", "minimum"]:
                    # Set to minimum
                    slider.set_value(slider.min_value())
                    print(f"[GUI] Set slider to minimum", file=sys.stderr)
                elif slider_value.lower() in ["fast", "fastest", "max", "maximum"]:
                    # Set to maximum
                    slider.set_value(slider.max_value())
                    print(f"[GUI] Set slider to maximum", file=sys.stderr)
                elif slider_value.lower() in ["medium", "middle", "mid"]:
                    # Set to middle
                    mid = (slider.min_value() + slider.max_value()) // 2
                    slider.set_value(mid)
                    print(f"[GUI] Set slider to middle", file=sys.stderr)

                # Click Apply/OK button (reuse parent variable defined earlier)
                apply_btn = self._find_control_fuzzy(parent, "Apply", ["Button"])
                if apply_btn:
                    apply_btn.click_input()
                    time.sleep(0.3)

                ok_btn = self._find_control_fuzzy(parent, "OK", ["Button"])
                if ok_btn:
                    ok_btn.click_input()

                return f"Successfully adjusted '{slider_name}' to '{slider_value}'"

            return "Navigation completed"

        except Exception as e:
            print(f"[GUI] Error: {e}", file=sys.stderr)
            raise Exception(f"GUI automation failed: {str(e)}")

    def _handle_volume_control_dynamic(self, action: Dict) -> str:
        """
        Dynamic multi-strategy volume control
        Tries multiple approaches to control volume without hardcoded paths
        """
        import subprocess

        action_value = action.get("value", "").lower()

        print(f"[GUI] === DYNAMIC VOLUME CONTROL ===", file=sys.stderr)
        print(f"[GUI] Target: {action_value}", file=sys.stderr)

        # Strategy 1: Try system tray volume icon (most reliable)
        print(f"[GUI] Strategy 1: System tray volume icon", file=sys.stderr)
        try:
            # Find taskbar
            taskbar = self._find_window_fuzzy(["taskbar", "notification"], timeout=3)
            if taskbar:
                # Try to find volume/speaker icon - Windows uses different names
                for icon_name in ["speakers", "volume", "sound", "audio", "notification chevron"]:
                    icon = self._find_control_fuzzy(taskbar, icon_name, ["Button"])
                    if icon:
                        print(f"[GUI] Found system tray icon: {icon_name}", file=sys.stderr)
                        icon.click_input()
                        time.sleep(1.5)

                        # Look for volume slider popup - try to find ANY slider
                        volume_window = self._find_window_fuzzy(["volume", "slider", "sound"], timeout=2)
                        if volume_window:
                            print(f"[GUI] Found volume popup window", file=sys.stderr)
                            return self._adjust_first_slider(volume_window, action_value)
                        break
        except Exception as e:
            print(f"[GUI] Strategy 1 failed: {e}", file=sys.stderr)

        # Strategy 2: Try Quick Settings (Windows 11)
        print(f"[GUI] Strategy 2: Quick Settings panel", file=sys.stderr)
        try:
            # Windows 11 quick settings
            quick_settings = self._find_window_fuzzy(["quick settings", "notification center"], timeout=2)
            if quick_settings:
                print(f"[GUI] Found Quick Settings", file=sys.stderr)
                return self._adjust_first_slider(quick_settings, action_value)
        except Exception as e:
            print(f"[GUI] Strategy 2 failed: {e}", file=sys.stderr)

        # Strategy 3: PowerShell command (most reliable fallback)
        print(f"[GUI] Strategy 3: PowerShell command", file=sys.stderr)
        try:
            if action_value in ["min", "minimum", "mute", "zero", "0"]:
                # Mute
                cmd = 'powershell -Command "(New-Object -ComObject WScript.Shell).SendKeys([char]173)"'
                subprocess.run(cmd, shell=True, check=True)
                return "Volume muted using PowerShell"
            elif action_value in ["max", "maximum", "unmute", "full", "100"]:
                # Set to max - first unmute, then set high
                subprocess.run('powershell -Command "$obj = New-Object -ComObject WScript.Shell; 1..50 | ForEach-Object { $obj.SendKeys([char]175) }"', shell=True, check=True, timeout=5)
                return "Volume set to maximum using PowerShell"
            elif action_value in ["medium", "middle", "mid", "50"]:
                # Medium volume
                subprocess.run('powershell -Command "$obj = New-Object -ComObject WScript.Shell; 1..25 | ForEach-Object { $obj.SendKeys([char]175) }"', shell=True, check=True, timeout=5)
                return "Volume set to medium using PowerShell"
        except Exception as e:
            print(f"[GUI] Strategy 3 failed: {e}", file=sys.stderr)

        # Strategy 4: Settings app as last resort
        print(f"[GUI] Strategy 4: Windows Settings app", file=sys.stderr)
        try:
            subprocess.Popen("start ms-settings:sound", shell=True)
            time.sleep(3)

            settings_window = self._find_window_fuzzy(["settings", "sound", "system"], timeout=3)
            if settings_window:
                print(f"[GUI] Found Settings window: {settings_window.window_text()}", file=sys.stderr)
                return self._adjust_first_slider(settings_window, action_value)
        except Exception as e:
            print(f"[GUI] Strategy 4 failed: {e}", file=sys.stderr)

        raise Exception("All volume control strategies failed. Please check if volume controls are accessible.")

    def _adjust_first_slider(self, parent_window, target_value: str) -> str:
        """
        Find and adjust the first available slider in a window
        Works with any slider without needing to know its name
        """
        print(f"[GUI] Searching for sliders in window: {parent_window.window_text()}", file=sys.stderr)

        slider = None
        try:
            # Find first slider dynamically
            for child in parent_window.descendants():
                try:
                    if child.element_info.control_type == "Slider":
                        slider = child
                        print(f"[GUI] Found slider: '{child.window_text()}'", file=sys.stderr)
                        break
                except:
                    continue
        except Exception as e:
            print(f"[GUI] Error searching for slider: {e}", file=sys.stderr)

        if not slider:
            # List all controls for debugging
            print(f"[GUI] Available controls:", file=sys.stderr)
            try:
                for child in parent_window.descendants():
                    try:
                        ctype = child.element_info.control_type
                        text = child.window_text()
                        print(f"[GUI]   - {ctype}: '{text}'", file=sys.stderr)
                    except:
                        pass
            except:
                pass
            raise Exception("No slider found in window")

        # Adjust slider based on target value
        if target_value in ["slow", "slowest", "min", "minimum", "mute", "zero", "0"]:
            slider.set_value(slider.min_value())
            print(f"[GUI] Set slider to minimum: {slider.min_value()}", file=sys.stderr)
        elif target_value in ["fast", "fastest", "max", "maximum", "unmute", "full", "100"]:
            slider.set_value(slider.max_value())
            print(f"[GUI] Set slider to maximum: {slider.max_value()}", file=sys.stderr)
        elif target_value in ["medium", "middle", "mid", "50"]:
            mid = (slider.min_value() + slider.max_value()) // 2
            slider.set_value(mid)
            print(f"[GUI] Set slider to middle: {mid}", file=sys.stderr)

        return f"Successfully adjusted volume to '{target_value}'"

    def click_ui_element(self, window_title: str, element_name: str, element_type: str = "Button") -> str:
        """
        Click a specific UI element in a window

        Args:
            window_title: Title or partial title of the window
            element_name: Name of the element to click
            element_type: Type of element (Button, Hyperlink, Text, etc.)

        Returns:
            Success message
        """
        try:
            # Find the window
            windows = self.desktop.windows()
            target_window = None

            for window in windows:
                try:
                    if window_title.lower() in window.window_text().lower():
                        target_window = window
                        break
                except:
                    continue

            if not target_window:
                raise Exception(f"Could not find window with title '{window_title}'")

            # Find and click the element
            element = target_window.child_window(title=element_name, control_type=element_type)
            element.click_input()

            return f"Clicked '{element_name}' in window '{window_title}'"

        except Exception as e:
            raise Exception(f"Failed to click element: {str(e)}")

    # ============================================================================
    # PRIMITIVE OPERATIONS - AI-DRIVEN ARCHITECTURE
    # ============================================================================

    def introspect_ui(self, window_search_terms: List[str], open_command: str = None) -> Dict:
        """
        PRIMITIVE OPERATION: Inspect UI and return complete structure for AI analysis.

        This is the core of the AI-driven approach - instead of hardcoding what to do,
        we return ALL available controls and let the AI decide.

        Args:
            window_search_terms: Terms to find the window (e.g., ["Settings", "Bluetooth"])
            open_command: Optional command to open the window first (e.g., "ms-settings:bluetooth")

        Returns:
            {
                "window": "Window title",
                "controls": [
                    {"name": "Bluetooth", "type": "ToggleButton", "state": "Off", "clickable": True},
                    {"name": "Add device", "type": "Button", "clickable": True},
                    ...
                ],
                "strategy": "Description of what was done"
            }
        """
        import subprocess

        print(f"[GUI INTROSPECT] Analyzing UI for: {window_search_terms}", file=sys.stderr)

        # Open window if command provided (using professional core)
        if open_command:
            # Check if it's a settings URI
            if "ms-settings" in open_command:
                target_window = self.gui_core.open_settings_page(open_command)
            else:
                print(f"[GUI INTROSPECT] Opening: {open_command}", file=sys.stderr)
                subprocess.Popen(open_command, shell=True)
                time.sleep(2)
                target_window = self.gui_core.find_window(window_search_terms, timeout=5)
        else:
            # Find the window using professional core
            target_window = self.gui_core.find_window(window_search_terms, timeout=5)

        if not target_window:
            return {
                "success": False,
                "error": f"Could not find window matching: {window_search_terms}",
                "window": None,
                "controls": []
            }

        window_title = target_window.window_text()
        print(f"[GUI INTROSPECT] Found window: {window_title}", file=sys.stderr)

        # Enumerate ALL controls
        controls = []
        try:
            for child in target_window.descendants():
                try:
                    control_type = child.element_info.control_type
                    name = child.window_text()

                    # Get state for toggles/checkboxes
                    state = None
                    try:
                        if control_type in ["ToggleButton", "CheckBox"]:
                            toggle_state = child.get_toggle_state()
                            state = "On" if toggle_state == 1 else "Off"
                    except:
                        pass

                    # Get value for sliders
                    value = None
                    try:
                        if control_type == "Slider":
                            value = {
                                "current": child.value(),
                                "min": child.min_value(),
                                "max": child.max_value()
                            }
                    except:
                        pass

                    # Determine if clickable/interactable
                    clickable = control_type in ["Button", "Hyperlink", "MenuItem", "ToggleButton", "CheckBox"]

                    # For unnamed toggle buttons, create a descriptive name
                    display_name = name
                    if not name or not name.strip():
                        if control_type == "ToggleButton" and state:
                            display_name = f"[Unnamed {control_type} - {state}]"
                        elif control_type in ["ToggleButton", "CheckBox"]:
                            display_name = f"[Unnamed {control_type}]"
                        else:
                            display_name = name  # Keep empty for other types

                    control_info = {
                        "name": display_name,
                        "type": control_type,
                        "clickable": clickable
                    }

                    if state:
                        control_info["state"] = state
                    if value:
                        control_info["value"] = value

                    # Include controls with names OR important unnamed controls (ToggleButton, CheckBox)
                    if (name and name.strip()) or control_type in ["ToggleButton", "CheckBox"]:
                        controls.append(control_info)

                except Exception as e:
                    continue

        except Exception as e:
            print(f"[GUI INTROSPECT] Error enumerating controls: {e}", file=sys.stderr)

        print(f"[GUI INTROSPECT] Found {len(controls)} controls", file=sys.stderr)

        # Print summary for debugging
        for ctrl in controls[:20]:  # First 20 controls
            state_str = f" ({ctrl.get('state', '')})" if 'state' in ctrl else ""
            print(f"[GUI INTROSPECT]   - {ctrl['type']}: '{ctrl['name']}'{state_str}", file=sys.stderr)

        return {
            "success": True,
            "window": window_title,
            "controls": controls,
            "strategy": f"Introspected {len(controls)} controls in '{window_title}'"
        }

    def execute_ui_action(self, window_search_terms: List[str], element_name: str,
                         action_type: str, value: any = None) -> str:
        """
        PRIMITIVE OPERATION: Execute generic action on any UI element.

        Args:
            window_search_terms: Terms to find the window
            element_name: Name of the element to interact with
            action_type: "click", "toggle", "set_value", etc.
            value: Value for set_value actions

        Returns:
            Success message
        """
        print(f"[GUI EXECUTE] Action: {action_type} on '{element_name}' (value={value})", file=sys.stderr)

        # Find the window using professional core
        target_window = self.gui_core.find_window(window_search_terms, timeout=5)

        if not target_window:
            raise Exception(f"Could not find window matching: {window_search_terms}")

        # Find the control using professional core (robust multi-strategy search)
        control = self.gui_core.find_control(target_window, name=element_name, partial_match=True)

        if not control:
            raise Exception(f"Could not find control '{element_name}' in window '{target_window.window_text()}'")

        control_type = control.element_info.control_type
        print(f"[GUI EXECUTE] Found {control_type}: '{control.window_text()}'", file=sys.stderr)

        # Execute action based on type using professional core
        if action_type == "click":
            if self.gui_core.click_control(control):
                return f"✓ Clicked '{element_name}'"
            else:
                raise Exception(f"Failed to click '{element_name}'")

        elif action_type == "toggle":
            if control_type in ["ToggleButton", "CheckBox"]:
                if self.gui_core.set_toggle(control, bool(value)):
                    return f"✓ Toggled '{element_name}' to {'On' if value else 'Off'}"
                else:
                    raise Exception(f"Failed to toggle '{element_name}'")
            else:
                # For non-toggle controls, just click
                if self.gui_core.click_control(control):
                    return f"✓ Clicked '{element_name}'"
                else:
                    raise Exception(f"Failed to click '{element_name}'")

        elif action_type == "set_value":
            try:
                if control_type == "Slider":
                    control.set_value(value)
                    return f"✓ Set '{element_name}' to {value}"
                else:
                    control.set_text(str(value))
                    return f"✓ Set '{element_name}' to {value}"
            except Exception as e:
                raise Exception(f"Failed to set value: {e}")

        else:
            raise Exception(f"Unknown action type: {action_type}")

    def ai_guided_navigation(self, goal: str, window_search_terms: List[str],
                            open_command: str = None, max_attempts: int = 3,
                            multi_step: bool = True) -> str:
        """
        AI-DRIVEN SELF-HEALING: Let AI analyze UI and decide what to do.

        This is the future-proof approach - AI introspects, decides, acts, verifies.

        Args:
            goal: What we're trying to achieve (e.g., "turn on bluetooth", "uninstall adobe")
            window_search_terms: Where to look
            open_command: Command to open the window
            max_attempts: Max retry attempts
            multi_step: If True, continues clicking through wizard dialogs until goal achieved

        Returns:
            Success message
        """
        import os
        from openai import OpenAI

        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        model = os.getenv('MODEL_NAME', 'gpt-4o-mini')

        print(f"[AI GUIDED] Goal: {goal}", file=sys.stderr)
        print(f"[AI GUIDED] Multi-step mode: {multi_step}", file=sys.stderr)
        print(f"[AI GUIDED] Using AI model to analyze and act", file=sys.stderr)

        steps_completed = []
        max_steps = 10 if multi_step else 1  # Limit wizard steps to prevent infinite loops

        for step_num in range(max_steps):
            if step_num > 0 and not multi_step:
                break  # Single-step mode

            print(f"\n[AI GUIDED] === Step {step_num + 1}/{max_steps} ===", file=sys.stderr)

            for attempt in range(max_attempts):
                print(f"[AI GUIDED] Attempt {attempt + 1}/{max_attempts}", file=sys.stderr)

                # Step 1: Introspect UI
                # DYNAMIC FIX: Detect Settings vs Wizard flows automatically
                # Settings: Stay in Settings window, navigate within it
                # Wizard: Look for dialog windows that appear during installation

                if step_num == 0:
                    # First step: use the original window search terms
                    search_terms = window_search_terms
                else:
                    # CRITICAL FIX: Detect if this is Settings navigation
                    # Check if goal OR window_search_terms mention Settings-related operations
                    goal_lower = goal.lower()
                    search_terms_str = ' '.join([str(t).lower() for t in window_search_terms])

                    # Settings-related keywords
                    settings_indicators = [
                        'settings', 'firewall', 'bluetooth', 'wifi', 'network', 'defender',
                        'display', 'sound', 'privacy', 'update', 'storage', 'personalization',
                        'system', 'turn off', 'turn on', 'enable', 'disable', 'toggle'
                    ]

                    # Check if this is a Settings operation
                    is_settings_operation = any(
                        indicator in goal_lower or indicator in search_terms_str
                        for indicator in settings_indicators
                    )

                    if is_settings_operation:
                        # Settings flow: Dynamic window matching
                        # Step 1: Use original search terms to find main Settings window
                        # Step 2+: Match ANY window (to handle new dialogs like "Customize Settings")
                        if step_num > 1:
                            # After initial navigation, match ANY non-excluded window
                            # This handles cases where new dialogs open with unpredictable titles
                            search_terms = [""]
                            print(f"[AI GUIDED] 🎯 Settings operation (step {step_num + 1}) - matching any window", file=sys.stderr)
                        else:
                            # First navigation step: use original window search terms
                            search_terms = window_search_terms
                            print(f"[AI GUIDED] 🎯 Settings operation (step {step_num + 1}) - using: {search_terms}", file=sys.stderr)
                    else:
                        # Wizard/Dialog flow: Look for popup windows
                        search_terms = ["", "wizard", "install", "uninstall", "setup", "dialog"]
                        print(f"[AI GUIDED] 📦 Wizard/Dialog flow detected - looking for popup windows", file=sys.stderr)

                ui_info = self.introspect_ui(search_terms, open_command if step_num == 0 and attempt == 0 else None)

                if not ui_info["success"]:
                    if attempt == max_attempts - 1:
                        # If we're past step 0, goal might be complete
                        if step_num > 0:
                            print(f"[AI GUIDED] No more windows found - assuming goal complete", file=sys.stderr)
                            return f"Goal achieved after {step_num} steps: {', '.join(steps_completed)}"
                        raise Exception(f"Failed to find window: {ui_info.get('error')}")
                    time.sleep(1)
                    continue

                # Step 2: Filter out already-clicked controls
                clicked_elements = set()
                for step in steps_completed:
                    # Extract element name from "Clicked 'ElementName'" format
                    if "Clicked '" in step:
                        elem_name = step.split("Clicked '")[1].split("'")[0]
                        clicked_elements.add(elem_name)

                # Remove already-clicked controls from the list
                available_controls = [
                    ctrl for ctrl in ui_info['controls']
                    if ctrl['name'] not in clicked_elements
                ]

                steps_context = f"Steps completed so far: {steps_completed}" if steps_completed else "This is the first step"
                ai_prompt = f"""You are analyzing a Windows UI to achieve this goal: "{goal}"

{steps_context}

Window: {ui_info['window']}

Available controls (already-clicked elements have been removed):
{json.dumps(available_controls, indent=2)}

CRITICAL RULES:
1. For "turn on/off" goals: Look for controls with type "ToggleButton" or "Button" with state "Off"/"On"
2. NEVER click the same element twice - if you already clicked it, try a different control
3. AVOID clicking navigation elements (like "Bluetooth & devices", "System") if you already navigated
4. Prioritize: ToggleButton > Button > Hyperlink > Text
5. For toggle operations: use action_type "click" on the ToggleButton (clicking toggles it)

Common patterns:
- Bluetooth toggle: Look for ToggleButton with state "Off" or "On"
- Settings navigation: Click categories once, then find the actual control
- Uninstall wizards: "Uninstall", "Next", "Yes", "Confirm", "Finish", "Close", "OK"

Respond with ONLY a JSON object:
{{
  "element_name": "exact name of control to interact with",
  "action_type": "click|toggle|set_value",
  "value": true/false for toggle, number for slider, or null for click,
  "reasoning": "brief explanation of why this is the next step"
}}

If the goal is already achieved (no more buttons to click), respond with:
{{
  "status": "complete",
  "reasoning": "explanation"
}}

If you cannot find the right control, respond with:
{{
  "status": "not_found",
  "reasoning": "explanation"
}}
"""

                try:
                    response = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": "You are a Windows UI automation expert. Analyze UI and decide the NEXT action in a multi-step process."},
                            {"role": "user", "content": ai_prompt}
                        ],
                        temperature=0.1,
                        max_tokens=500
                    )

                    ai_decision = response.choices[0].message.content.strip()

                    # Parse AI response
                    if ai_decision.startswith('```'):
                        ai_decision = ai_decision.strip('`').strip()
                        if ai_decision.startswith('json'):
                            ai_decision = ai_decision[4:].strip()

                    decision = json.loads(ai_decision)

                    print(f"[AI GUIDED] AI Decision: {json.dumps(decision, indent=2)}", file=sys.stderr)

                    # Check status
                    if decision.get("status") == "complete":
                        return f"Goal achieved after {len(steps_completed)} steps: {', '.join(steps_completed)}"

                    if decision.get("status") == "not_found":
                        if attempt == max_attempts - 1:
                            if step_num > 0:
                                # Might be done
                                return f"Goal likely achieved after {len(steps_completed)} steps: {', '.join(steps_completed)}"
                            raise Exception(f"AI could not find control: {decision.get('reasoning')}")
                        continue

                    # Step 3: Execute AI's decision
                    result = self.execute_ui_action(
                        search_terms,
                        decision["element_name"],
                        decision["action_type"],
                        decision.get("value")
                    )

                    step_description = f"Clicked '{decision['element_name']}'"
                    steps_completed.append(step_description)
                    print(f"[AI GUIDED] ✓ Step {step_num + 1}: {step_description}", file=sys.stderr)

                    # Wait for next window/dialog to appear
                    time.sleep(2)

                    # Break attempt loop, continue to next step
                    break

                except json.JSONDecodeError as e:
                    print(f"[AI GUIDED] Failed to parse AI response: {e}", file=sys.stderr)
                    if attempt == max_attempts - 1:
                        raise Exception(f"AI returned invalid response: {ai_decision[:200]}")
                    continue

                except Exception as e:
                    print(f"[AI GUIDED] Error: {e}", file=sys.stderr)
                    if attempt == max_attempts - 1:
                        if step_num > 0:
                            # Might be done
                            return f"Goal completed after {len(steps_completed)} steps: {', '.join(steps_completed)}"
                        raise
                    time.sleep(1)
                    continue

        # Completed all steps
        return f"Goal achieved after {len(steps_completed)} steps: {', '.join(steps_completed)}"
