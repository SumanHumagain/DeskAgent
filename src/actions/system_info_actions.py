"""
System Information Actions - Read system state without UI interaction
"""

import sys
import psutil
from typing import Dict


class SystemInfoActions:
    """Handles system information queries using APIs (no UI needed)"""

    def get_battery_status(self) -> Dict:
        """
        Get battery status using psutil (Windows API wrapper)

        Returns:
            Dictionary with battery information
        """
        try:
            battery = psutil.sensors_battery()

            if battery is None:
                return {
                    "error": "No battery found (desktop PC or battery not detected)",
                    "percentage": None,
                    "plugged_in": None,
                    "time_remaining": None
                }

            # Calculate time remaining
            time_remaining = None
            if battery.secsleft != psutil.POWER_TIME_UNLIMITED and battery.secsleft != psutil.POWER_TIME_UNKNOWN:
                hours = battery.secsleft // 3600
                minutes = (battery.secsleft % 3600) // 60
                time_remaining = f"{hours}h {minutes}m"

            status = "Charging" if battery.power_plugged else "Discharging"
            if battery.percent == 100 and battery.power_plugged:
                status = "Fully charged"

            result = {
                "percentage": battery.percent,
                "plugged_in": battery.power_plugged,
                "status": status,
                "time_remaining": time_remaining
            }

            print(f"[SYSTEM INFO] Battery: {battery.percent}% - {status}", file=sys.stderr)

            return result

        except Exception as e:
            raise Exception(f"Failed to get battery status: {str(e)}")

    def get_system_info(self) -> Dict:
        """
        Get general system information

        Returns:
            Dictionary with system info
        """
        try:
            import platform

            info = {
                "os": platform.system(),
                "os_version": platform.version(),
                "os_release": platform.release(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "cpu_count": psutil.cpu_count(),
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "memory_used_gb": round(psutil.virtual_memory().used / (1024**3), 2),
                "memory_percent": psutil.virtual_memory().percent
            }

            print(f"[SYSTEM INFO] OS: {info['os']} {info['os_release']}", file=sys.stderr)

            return info

        except Exception as e:
            raise Exception(f"Failed to get system info: {str(e)}")

    def get_disk_usage(self, path: str = "C:\\") -> Dict:
        """
        Get disk usage for a drive

        Args:
            path: Drive path (default: C:\\)

        Returns:
            Dictionary with disk usage info
        """
        try:
            usage = psutil.disk_usage(path)

            result = {
                "drive": path,
                "total_gb": round(usage.total / (1024**3), 2),
                "used_gb": round(usage.used / (1024**3), 2),
                "free_gb": round(usage.free / (1024**3), 2),
                "percent_used": usage.percent
            }

            print(f"[SYSTEM INFO] Disk {path}: {usage.percent}% used ({result['free_gb']}GB free)", file=sys.stderr)

            return result

        except Exception as e:
            raise Exception(f"Failed to get disk usage: {str(e)}")

    def get_top_processes_by_memory(self, limit: int = 5, exclude_fields: list = None) -> Dict:
        """
        Get top processes by memory usage

        Args:
            limit: Number of top processes to return (default: 5)
            exclude_fields: List of fields to exclude from output (e.g., ['pid', 'memory_percent'])

        Returns:
            Dictionary with top processes and their memory usage
        """
        try:
            processes = []
            exclude_fields = exclude_fields or []

            # Get all processes
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'memory_info']):
                try:
                    # Get process info
                    pinfo = proc.info
                    memory_mb = pinfo['memory_info'].rss / (1024 * 1024)  # Convert to MB
                    memory_percent = pinfo['memory_percent']

                    # Build process dict dynamically based on exclusions
                    proc_data = {}

                    # Always include name (required)
                    proc_data['name'] = pinfo['name']

                    # Conditionally add other fields
                    if 'pid' not in exclude_fields:
                        proc_data['pid'] = pinfo['pid']
                    if 'memory_mb' not in exclude_fields:
                        proc_data['memory_mb'] = round(memory_mb, 2)
                    if 'memory_percent' not in exclude_fields:
                        proc_data['memory_percent'] = round(memory_percent, 2)

                    # Store raw memory_mb for sorting even if excluded from display
                    if 'memory_mb' not in proc_data:
                        proc_data['_memory_mb_for_sort'] = round(memory_mb, 2)

                    processes.append(proc_data)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass

            # Sort by memory usage and get top N
            # Use _memory_mb_for_sort if memory_mb was excluded
            sort_key = '_memory_mb_for_sort' if 'memory_mb' in exclude_fields else 'memory_mb'
            top_processes = sorted(processes, key=lambda x: x.get(sort_key, x.get('memory_mb', 0)), reverse=True)[:limit]

            # Remove sorting helper field if it exists
            for proc in top_processes:
                proc.pop('_memory_mb_for_sort', None)

            result = {
                "top_processes": top_processes,
                "total_count": len(processes),
                "exclude_fields": exclude_fields  # Pass through for frontend formatting
            }

            exclusion_str = f" (excluding: {', '.join(exclude_fields)})" if exclude_fields else ""
            print(f"[SYSTEM INFO] Top {limit} processes by memory usage retrieved{exclusion_str}", file=sys.stderr)

            return result

        except Exception as e:
            raise Exception(f"Failed to get top processes: {str(e)}")
