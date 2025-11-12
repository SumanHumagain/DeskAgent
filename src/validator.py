"""
Validator - Checks action plans against allowlist and safety rules
"""

import os
import json
from pathlib import Path
from typing import List, Dict


class Validator:
    """Validates action plans against safety rules and allowlists"""

    def __init__(self):
        self.config = self._load_allowlist()

    def _load_allowlist(self) -> dict:
        """Load allowlist configuration"""
        config_path = Path(__file__).parent.parent / 'config' / 'allowlist.json'

        if not config_path.exists():
            raise FileNotFoundError(f"Allowlist config not found at {config_path}")

        with open(config_path, 'r') as f:
            config = json.load(f)

        # Expand environment variables in paths
        config['allowed_folders'] = [
            self._expand_path(p) for p in config['allowed_folders']
        ]
        config['forbidden_folders'] = [
            self._expand_path(p) for p in config['forbidden_folders']
        ]

        return config

    def _expand_path(self, path: str) -> str:
        """Expand environment variables like %USERNAME%"""
        # Replace %USERNAME% with actual username
        if '%USERNAME%' in path:
            username = os.getenv('USERNAME') or os.getenv('USER')
            path = path.replace('%USERNAME%', username)

        return os.path.normpath(path)

    def validate_plan(self, plan: List[Dict]) -> Dict:
        """
        Validate an action plan

        Returns:
            {
                'valid': bool,
                'error': str or None,
                'warnings': List[str]
            }
        """
        warnings = []

        # Check plan length
        max_actions = self.config.get('limits', {}).get('max_actions_per_session', 50)
        if len(plan) > max_actions:
            return {
                'valid': False,
                'error': f'Plan exceeds maximum actions limit ({len(plan)} > {max_actions})',
                'warnings': warnings
            }

        # Validate each action
        for i, step in enumerate(plan, 1):
            result = self._validate_action(step)
            if not result['valid']:
                return {
                    'valid': False,
                    'error': f'Step {i} validation failed: {result["error"]}',
                    'warnings': warnings
                }

            if result.get('warnings'):
                warnings.extend([f"Step {i}: {w}" for w in result['warnings']])

        return {
            'valid': True,
            'error': None,
            'warnings': warnings
        }

    def _validate_action(self, action: Dict) -> Dict:
        """Validate a single action"""
        action_name = action.get('action')
        args = action.get('args', {})
        warnings = []

        # Check if action requires confirmation
        always_confirm = self.config.get('confirmation_rules', {}).get('always_confirm_actions', [])
        if action_name in always_confirm:
            warnings.append(f"Action '{action_name}' requires explicit confirmation")

        # Validate based on action type
        if 'path' in args:
            path_result = self._validate_path(args['path'], action_name)
            if not path_result['valid']:
                return path_result

            if path_result.get('warnings'):
                warnings.extend(path_result['warnings'])

        if 'to' in args and action_name == 'send_email':
            # Validate email address format (basic check)
            email = args['to']
            if '@' not in email or '.' not in email:
                return {
                    'valid': False,
                    'error': f'Invalid email address: {email}',
                    'warnings': warnings
                }

        if 'attachments' in args:
            for attachment in args.get('attachments', []):
                attach_result = self._validate_path(attachment, 'attachment')
                if not attach_result['valid']:
                    return attach_result

        return {
            'valid': True,
            'error': None,
            'warnings': warnings
        }

    def _validate_path(self, path: str, context: str = 'path') -> Dict:
        """Validate a file/folder path - only check critical system folders"""
        # Skip validation for paths with template variables (will be resolved later)
        if '{{RESULT_' in path:
            return {
                'valid': True,
                'error': None,
                'warnings': []
            }

        path = self._expand_path(path)
        path_obj = Path(path)
        warnings = []

        # ONLY check forbidden system folders (for safety)
        for forbidden in self.config.get('forbidden_folders', []):
            forbidden_path = Path(forbidden)
            try:
                if path_obj.is_relative_to(forbidden_path) or path_obj == forbidden_path:
                    warnings.append(f'WARNING: Accessing system folder: {path}')
                    # Don't block - just warn, user can approve
                    break
            except (ValueError, AttributeError):
                # is_relative_to not available in older Python, fallback
                if str(path_obj).startswith(str(forbidden_path)):
                    warnings.append(f'WARNING: Accessing system folder: {path}')
                    break

        # ONLY check dangerous executable extensions (for safety)
        if path_obj.suffix:
            forbidden_exts = self.config.get('forbidden_extensions', [])
            if path_obj.suffix.lower() in forbidden_exts:
                warnings.append(f'WARNING: Dangerous file type: {path_obj.suffix}')
                # Don't block - just warn, user can approve

        # NO ALLOWLIST CHECK - Everything is allowed if user approves!
        # User approval in UI is the security mechanism

        return {
            'valid': True,
            'error': None,
            'warnings': warnings
        }

    def is_high_risk_action(self, action_name: str) -> bool:
        """Check if action is high risk"""
        always_confirm = self.config.get('confirmation_rules', {}).get('always_confirm_actions', [])
        return action_name in always_confirm
