#!/usr/bin/env python3
"""
Desktop Automation Agent - Main CLI Entry Point
"""

import argparse
import sys
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from planner import Planner
from validator import Validator
from executor import Executor
from logger import AuditLogger

console = Console()


def print_banner():
    """Display welcome banner"""
    banner = """
    [bold cyan]Desktop Automation Agent[/bold cyan]
    [dim]AI-powered desktop control via natural language[/dim]

    Type your command or 'help' for assistance
    Press Ctrl+C to exit
    """
    console.print(Panel(banner, border_style="cyan"))


def print_help():
    """Display help information"""
    help_text = """
    [bold]Example Commands:[/bold]

    • "Open my Downloads folder"
    • "Find the latest PDF in Documents"
    • "Create a file on Desktop called todo.txt with content 'Buy milk'"
    • "Email me the report from Downloads"

    [bold]Special Commands:[/bold]

    • help - Show this help message
    • logs - View recent action logs
    • exit/quit - Exit the application
    """
    console.print(Panel(help_text, title="Help", border_style="green"))


def view_logs(logger: AuditLogger, limit: int = 10):
    """Display recent audit logs"""
    logs = logger.get_recent_logs(limit)

    if not logs:
        console.print("[yellow]No logs found[/yellow]")
        return

    console.print(f"\n[bold]Recent Actions (last {limit}):[/bold]\n")

    for log in logs:
        status_color = "green" if log['status'] == 'success' else "red"
        console.print(f"[dim]{log['timestamp']}[/dim]")
        console.print(f"  Action: [cyan]{log['action']}[/cyan]")
        console.print(f"  Status: [{status_color}]{log['status']}[/{status_color}]")
        if log.get('error'):
            console.print(f"  Error: [red]{log['error']}[/red]")
        console.print()


def display_plan(plan: list) -> bool:
    """
    Display the planned actions and ask for user confirmation
    Returns True if user approves, False otherwise
    """
    console.print("\n[bold yellow]Planned Actions:[/bold yellow]\n")

    risk_colors = {
        'low': 'green',
        'medium': 'yellow',
        'high': 'red'
    }

    for i, step in enumerate(plan, 1):
        action = step.get('action', 'unknown')
        args = step.get('args', {})
        risk = step.get('risk_level', 'medium')
        color = risk_colors.get(risk, 'yellow')

        console.print(f"{i}. [{color}]●[/{color}] [bold]{action}[/bold]")

        for key, value in args.items():
            console.print(f"     {key}: [cyan]{value}[/cyan]")

        console.print()

    return Confirm.ask("\n[bold]Execute these actions?[/bold]", default=True)


def interactive_mode(args):
    """Run the agent in interactive CLI mode"""
    # Load environment variables
    load_dotenv()

    # Initialize components
    planner = Planner()
    validator = Validator()
    executor = Executor()
    logger = AuditLogger()

    print_banner()

    if args.dry_run:
        console.print("[yellow]Running in DRY RUN mode - actions will not be executed[/yellow]\n")

    while True:
        try:
            # Get user prompt
            prompt = Prompt.ask("\n[bold green]>[/bold green]", default="")

            if not prompt.strip():
                continue

            # Handle special commands
            if prompt.lower() in ['exit', 'quit', 'q']:
                console.print("[yellow]Goodbye![/yellow]")
                break

            if prompt.lower() == 'help':
                print_help()
                continue

            if prompt.lower() == 'logs':
                view_logs(logger)
                continue

            # Step 1: Plan
            console.print("\n[dim]Planning actions...[/dim]")
            plan = planner.create_plan(prompt)

            if not plan:
                console.print("[red]Failed to create a valid plan. Please try rephrasing your request.[/red]")
                continue

            # Step 2: Validate
            console.print("[dim]Validating actions...[/dim]")
            validation_result = validator.validate_plan(plan)

            if not validation_result['valid']:
                console.print(f"[red]Validation failed:[/red] {validation_result['error']}")
                continue

            # Step 3: Confirm (unless auto-approve or dry-run)
            if not args.yes and not args.dry_run:
                approved = display_plan(plan)
                if not approved:
                    console.print("[yellow]Action cancelled by user[/yellow]")
                    continue
            else:
                display_plan(plan)

            # Step 4: Execute
            if args.dry_run:
                console.print("\n[yellow]DRY RUN - Skipping execution[/yellow]")
            else:
                console.print("\n[dim]Executing actions...[/dim]\n")
                results = executor.execute_plan(plan)

                # Step 5: Report results
                success_count = sum(1 for r in results if r['status'] == 'success')
                total_count = len(results)

                if success_count == total_count:
                    console.print(f"\n[bold green]✓ All actions completed successfully ({success_count}/{total_count})[/bold green]")
                else:
                    console.print(f"\n[bold yellow]⚠ Completed with issues ({success_count}/{total_count} successful)[/bold yellow]")

                # Log results
                for result in results:
                    logger.log_action(
                        action=result['action'],
                        args=result.get('args', {}),
                        status=result['status'],
                        error=result.get('error')
                    )

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted by user[/yellow]")
            if Confirm.ask("Exit?", default=False):
                break

        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")
            if args.debug:
                raise


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Desktop Automation Agent - Control your PC with natural language'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview actions without executing them'
    )

    parser.add_argument(
        '-y', '--yes',
        action='store_true',
        help='Auto-approve all actions (skip confirmation)'
    )

    parser.add_argument(
        '--view-logs',
        action='store_true',
        help='View recent action logs and exit'
    )

    parser.add_argument(
        '--tail',
        type=int,
        default=10,
        metavar='N',
        help='Number of log entries to show (default: 10)'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode with full error traces'
    )

    args = parser.parse_args()

    # Handle view-logs mode
    if args.view_logs:
        load_dotenv()
        logger = AuditLogger()
        view_logs(logger, args.tail)
        return

    # Run interactive mode
    interactive_mode(args)


if __name__ == '__main__':
    main()
