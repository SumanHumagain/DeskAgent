"""
System Information Actions
Handles queries about system status, processes, hardware, etc.
"""

import psutil
import platform
from typing import Dict, List


class SystemInfoActions:
    """Handles system information queries"""

    def __init__(self):
        """Initialize system info actions"""
        pass

    def get_top_processes_by_memory(self, limit: int = 5, exclude_fields: list = None) -> Dict:
        """
        Get top processes by memory usage with dynamic field exclusion

        Args:
            limit: Number of top processes to return
            exclude_fields: List of fields to exclude from output (e.g., ['pid', 'memory_percent'])

        Returns:
            Dictionary with top processes information
        """
        processes = []
        exclude_fields = exclude_fields or []

        try:
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'memory_info']):
                try:
                    pinfo = proc.info
                    memory_mb = pinfo['memory_info'].rss / (1024 * 1024)  # Convert to MB
                    memory_percent = pinfo['memory_percent'] or 0

                    # Build process dict dynamically based on exclusions
                    proc_data = {}
                    proc_data['name'] = pinfo['name']  # Always include name

                    if 'pid' not in exclude_fields:
                        proc_data['pid'] = pinfo['pid']
                    if 'memory_mb' not in exclude_fields:
                        proc_data['memory_mb'] = round(memory_mb, 2)
                    if 'memory_percent' not in exclude_fields:
                        proc_data['memory_percent'] = round(memory_percent, 2)

                    # Store raw memory_mb for sorting even if excluded
                    if 'memory_mb' not in proc_data:
                        proc_data['_memory_mb_for_sort'] = round(memory_mb, 2)

                    processes.append(proc_data)

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Sort by memory (use _memory_mb_for_sort if memory_mb is excluded)
            processes.sort(
                key=lambda x: x.get('memory_mb', x.get('_memory_mb_for_sort', 0)),
                reverse=True
            )

            # Remove the sort helper field
            for proc in processes:
                proc.pop('_memory_mb_for_sort', None)

            # Get top N
            top_processes = processes[:limit]

            return {
                'top_processes': top_processes,
                'total_processes': len(processes),
                'limit': limit
            }

        except Exception as e:
            raise Exception(f"Failed to get process information: {str(e)}")

    def get_system_info(self) -> Dict:
        """
        Get general system information

        Returns:
            Dictionary with system information
        """
        try:
            return {
                'os': platform.system(),
                'os_version': platform.version(),
                'os_release': platform.release(),
                'architecture': platform.machine(),
                'processor': platform.processor(),
                'cpu_count': psutil.cpu_count(),
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
                'memory_used_gb': round(psutil.virtual_memory().used / (1024**3), 2),
                'memory_percent': psutil.virtual_memory().percent
            }
        except Exception as e:
            raise Exception(f"Failed to get system information: {str(e)}")

    def get_disk_usage(self, path: str = "C:\\") -> Dict:
        """
        Get disk usage for a specific path

        Args:
            path: Path to check (default: C:\\)

        Returns:
            Dictionary with disk usage information
        """
        try:
            usage = psutil.disk_usage(path)
            return {
                'path': path,
                'total_gb': round(usage.total / (1024**3), 2),
                'used_gb': round(usage.used / (1024**3), 2),
                'free_gb': round(usage.free / (1024**3), 2),
                'percent_used': usage.percent
            }
        except Exception as e:
            raise Exception(f"Failed to get disk usage: {str(e)}")

    def get_battery_status(self) -> Dict:
        """
        Get battery status (for laptops)

        Returns:
            Dictionary with battery information or None if no battery
        """
        try:
            battery = psutil.sensors_battery()
            if battery is None:
                return {
                    'has_battery': False,
                    'message': 'No battery detected (desktop or AC-only device)'
                }

            return {
                'has_battery': True,
                'percent': battery.percent,
                'power_plugged': battery.power_plugged,
                'time_left_minutes': battery.secsleft // 60 if battery.secsleft != psutil.POWER_TIME_UNLIMITED else None
            }
        except Exception as e:
            raise Exception(f"Failed to get battery status: {str(e)}")
