"""
Tick-Tock Widget Package

A comprehensive project time tracking widget built with Python and Tkinter.
This package provides an intuitive interface for tracking time spent on
various projects and their sub-activities.
"""

__version__ = "0.1.0"
__author__ = "Will-cz"
__email__ = "will-cz@users.noreply.github.com"

from .tick_tock_widget import TickTockWidget, main
from .project_data import ProjectDataManager, Project, SubActivity, TimeRecord
from .theme_colors import ThemeColors
from .project_management import ProjectManagementWindow
from .monthly_report import MonthlyReportWindow
from .minimized_widget import MinimizedTickTockWidget
from .config import Config, Environment, get_config, init_config, reset_config

__all__ = [
    "TickTockWidget",
    "main",
    "ProjectDataManager",
    "Project",
    "SubActivity",
    "TimeRecord",
    "ThemeColors",
    "ProjectManagementWindow",
    "MonthlyReportWindow",
    "MinimizedTickTockWidget",
    "Config",
    "Environment",
    "get_config",
    "init_config",
    "reset_config",
]
