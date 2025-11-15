"""
Utility modules for Desktop Automation Agent
"""

from .admin_elevation import AdminElevation, is_admin, require_admin

__all__ = ['AdminElevation', 'is_admin', 'require_admin']
