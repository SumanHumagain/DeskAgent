"""
Executor - Orchestrates execution of action plans
"""

import os
import sys
from typing import List, Dict
from pathlib import Path

# Import action handlers
from actions.file_actions import FileActions
from actions.app_actions import AppActions
from actions.email_actions import EmailActions
from actions.gui_actions import GUIActions
from actions.code_executor import CodeExecutor
from actions.system_info_actions import SystemInfoActions
from actions.bluetooth_action import BluetoothAction


class Executor:
    """Executes validated action plans"""

    def __init__(self):
        # Initialize action handlers
        self.file_actions = FileActions()
        self.app_actions = AppActions()
        self.email_actions = EmailActions()
        self.gui_actions = GUIActions()
        self.code_executor = CodeExecutor()
        self.system_info_actions = SystemInfoActions()
        self.bluetooth_action = BluetoothAction()

        # Action registry - maps action names to handler methods
        self.action_handlers = {
            'open_folder': self.file_actions.open_folder,
            'find_file': self.file_actions.find_file,
            'create_file': self.file_actions.create_file,
            'open_file': self.file_actions.open_file,
            'list_files': self.file_actions.list_files,
            'show_file_in_explorer': self.file_actions.show_file_in_explorer,
            'copy_file': self.file_actions.copy_file,
            'move_file': self.file_actions.move_file,
            'delete_file': self.file_actions.delete_file,
            'send_email': self.email_actions.send_email,
            'launch_app': self.app_actions.launch_app,
            'navigate_settings': self.gui_actions.navigate_control_panel_settings,
            # AI-DRIVEN ACTIONS (New Architecture)
            'ai_navigate': self.gui_actions.ai_guided_navigation,
            'introspect_ui': self.gui_actions.introspect_ui,
            'execute_ui_action': self.gui_actions.execute_ui_action,
            # META-PRIMITIVE: Dynamic code execution (OpenAI generates, we execute)
            'run_python_code': self.code_executor.run_python_code,
            'run_powershell': self.code_executor.run_powershell,
            # SYSTEM INFO ACTIONS
            'get_top_processes_by_memory': self.system_info_actions.get_top_processes_by_memory,
            # BLUETOOTH ACTIONS (Professional state-checking implementation)
            'bluetooth_on': self.bluetooth_action.turn_on,
            'bluetooth_off': self.bluetooth_action.turn_off,
            'bluetooth_toggle': self.bluetooth_action.toggle,
            'bluetooth_state': self.bluetooth_action.get_bluetooth_state,
            'chat': self._handle_chat,
        }

    def execute_plan(self, plan: List[Dict]) -> List[Dict]:
        """
        Execute a validated action plan with support for result chaining

        Args:
            plan: List of action dictionaries

        Returns:
            List of result dictionaries with status and output
        """
        results = []

        for i, step in enumerate(plan):
            # Resolve any references to previous results
            step = self._resolve_references(step, results)

            result = self._execute_action(step)
            results.append(result)

            # Stop execution on critical failure
            if result['status'] == 'error' and result.get('critical', False):
                print(f"Critical error encountered. Stopping execution.", file=sys.stderr)
                break

        return results

    def _resolve_references(self, step: Dict, previous_results: List[Dict]) -> Dict:
        """
        Resolve references to previous action results in the current step
        Supports syntax like: {{RESULT_0.files[0].path}}
        """
        import json
        import re

        # Work directly with the dict to avoid JSON escaping issues
        def resolve_value(value, previous_results):
            """Recursively resolve references in any value"""
            if isinstance(value, str):
                # Find all references like {{RESULT_X.path.to.value}}
                pattern = r'\{\{RESULT_(\d+)(\.[\w\[\].]+)?\}\}'

                def replace_ref(match):
                    result_index = int(match.group(1))
                    path = match.group(2) if match.group(2) else ''

                    if result_index >= len(previous_results):
                        return match.group(0)

                    result = previous_results[result_index]
                    resolved_value = result.get('output')

                    if path and resolved_value:
                        try:
                            for part in path.strip('.').split('.'):
                                if '[' in part and ']' in part:
                                    key = part.split('[')[0]
                                    index = int(part.split('[')[1].split(']')[0])
                                    resolved_value = resolved_value[key][index] if key else resolved_value[index]
                                else:
                                    resolved_value = resolved_value[part]
                        except (KeyError, IndexError, TypeError):
                            return match.group(0)

                    return str(resolved_value) if resolved_value is not None else match.group(0)

                return re.sub(pattern, replace_ref, value)

            elif isinstance(value, dict):
                return {k: resolve_value(v, previous_results) for k, v in value.items()}

            elif isinstance(value, list):
                return [resolve_value(item, previous_results) for item in value]

            else:
                return value

        return resolve_value(step, previous_results)

    def _execute_action(self, action: Dict) -> Dict:
        """Execute a single action"""
        action_name = action.get('action')
        args = action.get('args', {})

        result = {
            'action': action_name,
            'args': args,
            'status': 'unknown',
            'output': None,
            'error': None
        }

        try:
            # Get handler for this action
            handler = self.action_handlers.get(action_name)

            if not handler:
                result['status'] = 'error'
                result['error'] = f'Unknown action: {action_name}'
                result['critical'] = False
                return result

            # Execute the action
            print(f"  Executing: {action_name} with args {args}", file=sys.stderr)
            output = handler(**args)

            result['status'] = 'success'
            result['output'] = output

        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            result['critical'] = False
            print(f"  Error: {str(e)}", file=sys.stderr)

        return result

    def _handle_chat(self, message: str) -> str:
        """Handle chat/conversational messages"""
        return message

    def get_supported_actions(self) -> List[str]:
        """Return list of supported action names"""
        return list(self.action_handlers.keys())
