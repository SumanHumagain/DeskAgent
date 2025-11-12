#!/usr/bin/env python3
"""
API Wrapper for Desktop Automation Agent
Provides JSON-based API for Electron UI
"""

import argparse
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from planner import Planner
from validator import Validator
from executor import Executor
from logger import AuditLogger
from utils.admin_elevation import AdminElevation, is_admin


def create_plan_from_prompt(prompt: str, conversation_history: list = None) -> dict:
    """
    Create a plan from a natural language prompt
    Returns: JSON object with success status and plan
    """
    try:
        load_dotenv()
        planner = Planner()
        validator = Validator()

        # Step 1: Create plan with conversation history
        plan = planner.create_plan(prompt, conversation_history)

        if not plan:
            return {
                'success': False,
                'error': 'Failed to create a valid plan. Please try rephrasing your request.'
            }

        # Step 2: Validate plan
        validation_result = validator.validate_plan(plan)

        if not validation_result['valid']:
            return {
                'success': False,
                'error': f"Validation failed: {validation_result['error']}"
            }

        # Return the validated plan
        return {
            'success': True,
            'plan': plan
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def execute_plan_from_json(plan_json: str) -> dict:
    """
    Execute a plan from JSON
    Returns: JSON object with execution results
    """
    try:
        load_dotenv()
        executor = Executor()
        logger = AuditLogger()

        # Parse the plan
        plan = json.loads(plan_json)

        # Execute the plan
        results = executor.execute_plan(plan)

        # Log each action
        for result in results:
            logger.log_action(
                action=result['action'],
                args=result.get('args', {}),
                status=result['status'],
                output=result.get('output'),  # Store output for action chaining
                error=result.get('error')
            )

        return {
            'success': True,
            'results': results
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def get_logs(limit: int = 10) -> dict:
    """
    Get recent logs
    Returns: JSON object with logs
    """
    try:
        load_dotenv()
        logger = AuditLogger()

        logs = logger.get_recent_logs(limit)

        return {
            'success': True,
            'logs': logs
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def main():
    """Main entry point for API wrapper"""
    parser = argparse.ArgumentParser(
        description='API Wrapper for Desktop Automation Agent'
    )

    parser.add_argument(
        '--prompt',
        type=str,
        help='Natural language prompt to convert to plan'
    )

    parser.add_argument(
        '--with-history',
        action='store_true',
        help='Read conversation history from stdin'
    )

    parser.add_argument(
        '--plan-only',
        action='store_true',
        help='Only create the plan, do not execute'
    )

    parser.add_argument(
        '--execute-plan',
        action='store_true',
        help='Execute a plan from JSON (read from stdin)'
    )

    parser.add_argument(
        '--get-logs',
        type=int,
        help='Get N recent logs'
    )

    parser.add_argument(
        '--check-admin',
        action='store_true',
        help='Check administrator privilege status'
    )

    args = parser.parse_args()

    # Check admin status on startup and log
    admin_status = AdminElevation.get_admin_status()
    if args.execute_plan:
        # Only log for execution (not for planning)
        print(f"[ADMIN] {admin_status['message']}", file=sys.stderr)
        if not admin_status['is_admin']:
            print(f"[ADMIN] WARNING: {admin_status['recommendation']}", file=sys.stderr)
            print(f"[ADMIN] Some operations (firewall, bluetooth, etc.) may require administrator privileges", file=sys.stderr)

    result = None

    # Handle admin check
    if args.check_admin:
        result = admin_status
    # Handle different modes
    elif args.prompt:
        # Read conversation history from stdin if flag is set
        conversation_history = None
        if args.with_history:
            try:
                history_json = sys.stdin.read()
                conversation_history = json.loads(history_json)
            except (json.JSONDecodeError, Exception):
                conversation_history = None

        result = create_plan_from_prompt(args.prompt, conversation_history)
    elif args.execute_plan:
        # Read plan from stdin
        plan_json = sys.stdin.read()
        result = execute_plan_from_json(plan_json)
    elif args.get_logs:
        result = get_logs(args.get_logs)
    else:
        result = {
            'success': False,
            'error': 'No valid operation specified'
        }

    # Output JSON result
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
