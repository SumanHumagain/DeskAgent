"""
Audit Logger - Logs all actions to SQLite database
"""

import os
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


class AuditLogger:
    """Logs all agent actions to SQLite for audit trail"""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # Default to logs/audit.db in project root
            project_root = Path(__file__).parent.parent
            logs_dir = project_root / 'logs'
            logs_dir.mkdir(exist_ok=True)
            db_path = logs_dir / 'audit.db'

        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize the database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                action TEXT NOT NULL,
                args TEXT,
                status TEXT NOT NULL,
                output TEXT,
                error TEXT,
                user TEXT
            )
        ''')

        conn.commit()
        conn.close()

    def log_action(
        self,
        action: str,
        args: Dict,
        status: str,
        output: Optional[str] = None,
        error: Optional[str] = None
    ):
        """
        Log an action to the database

        Args:
            action: Action name (e.g., 'open_folder')
            args: Action arguments as dict
            status: 'success' or 'error'
            output: Optional output from action
            error: Optional error message
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        timestamp = datetime.now().isoformat()
        user = os.getenv('USERNAME') or os.getenv('USER') or 'unknown'
        args_json = json.dumps(args)
        output_json = json.dumps(output) if output else None

        cursor.execute('''
            INSERT INTO actions (timestamp, action, args, status, output, error, user)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (timestamp, action, args_json, status, output_json, error, user))

        conn.commit()
        conn.close()

    def get_recent_logs(self, limit: int = 10) -> List[Dict]:
        """
        Get recent log entries

        Args:
            limit: Number of entries to retrieve

        Returns:
            List of log dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM actions
            ORDER BY id DESC
            LIMIT ?
        ''', (limit,))

        rows = cursor.fetchall()
        conn.close()

        logs = []
        for row in rows:
            log = {
                'id': row['id'],
                'timestamp': row['timestamp'],
                'action': row['action'],
                'args': json.loads(row['args']) if row['args'] else {},
                'status': row['status'],
                'output': json.loads(row['output']) if row['output'] else None,
                'error': row['error'],
                'user': row['user']
            }
            logs.append(log)

        return logs

    def get_statistics(self) -> Dict:
        """Get statistics about logged actions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Total actions
        cursor.execute('SELECT COUNT(*) FROM actions')
        total = cursor.fetchone()[0]

        # Success/error counts
        cursor.execute('SELECT status, COUNT(*) FROM actions GROUP BY status')
        status_counts = dict(cursor.fetchall())

        # Most common actions
        cursor.execute('''
            SELECT action, COUNT(*) as count
            FROM actions
            GROUP BY action
            ORDER BY count DESC
            LIMIT 5
        ''')
        common_actions = cursor.fetchall()

        conn.close()

        return {
            'total_actions': total,
            'successful': status_counts.get('success', 0),
            'failed': status_counts.get('error', 0),
            'most_common_actions': common_actions
        }

    def clear_old_logs(self, days: int = 30):
        """Delete logs older than specified days"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_date = cutoff_date.replace(day=cutoff_date.day - days)
        cutoff_str = cutoff_date.isoformat()

        cursor.execute('DELETE FROM actions WHERE timestamp < ?', (cutoff_str,))

        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        return deleted
