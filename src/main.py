"""
Tick-Tock Widget - Main Entry Point

A personal time tracking desktop application for Windows.
"""

import logging
from logging.handlers import RotatingFileHandler
import sys
from importlib.metadata import PackageNotFoundError, version as package_version
from pathlib import Path
from typing import Optional
import tkinter as tk
from tkinter import messagebox

from src.app_service import AppService
from src.config import Config
from src.instance import SingleInstance
from src.paths import user_data_dir
from src.projects import ProjectManager
from src import __version__ as module_version
from src.storage import RecoveryStatus, Storage
from src.ui.widget import TickTockWidget

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


def _configure_file_logging(level: int) -> Optional[Path]:
    """Attach a rotating file handler for persistent diagnostics."""
    log_path = user_data_dir() / "logs" / "tick_tock.log"
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        root_logger = logging.getLogger()
        existing = [
            h for h in root_logger.handlers if isinstance(h, RotatingFileHandler)
        ]
        if not existing:
            fh = RotatingFileHandler(
                log_path,
                maxBytes=1_000_000,
                backupCount=3,
                encoding="utf-8",
            )
            fh.setLevel(level)
            fh.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            )
            root_logger.addHandler(fh)
        return log_path
    except OSError as exc:
        logger.warning("Could not configure file logging at %s: %s", log_path, exc)
        return None


def _get_app_version() -> str:
    """Return app version from installed metadata or package fallback."""
    try:
        return package_version("tick-tock")
    except PackageNotFoundError:
        return module_version or "unknown"


def _show_already_running_dialog() -> None:
    """Show a friendly GUI notice when a second launch is attempted."""
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo(
            "Tick-Tock Already Running",
            "Tick-Tock is already running.\n"
            "The existing window has been asked to come to the front.",
            parent=root,
        )
        root.destroy()
    except Exception:  # pylint: disable=broad-except
        # Fallback to log-only behavior in environments without GUI support.
        logger.exception("Could not show already-running dialog")


def _show_fatal_crash_dialog(exc: Exception, log_path: Optional[Path]) -> None:
    """Show a fatal startup/runtime crash dialog for desktop users."""
    details = f"{type(exc).__name__}: {exc}"
    log_hint = f"\n\nLog file:\n{log_path}" if log_path is not None else ""
    message = (
        "Tick-Tock encountered an unrecoverable error and must close.\n\n"
        f"{details}{log_hint}"
    )
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Tick-Tock Crash", message, parent=root)
        root.destroy()
    except Exception:  # pylint: disable=broad-except
        logger.exception("Could not show fatal crash dialog")


def main() -> int:
    """Main entry point for the Tick-Tock Widget application."""
    config = Config()

    log_level = logging.DEBUG if config.debug else logging.INFO
    logging.getLogger().setLevel(log_level)
    log_path = _configure_file_logging(log_level)
    # Pillow emits optional plugin import debug noise in dev; keep PIL quieter
    # while leaving application debug logs intact.
    logging.getLogger("PIL").setLevel(logging.INFO)

    logger.info("Tick-Tock Widget - v%s", _get_app_version())
    logger.info("Environment: %s", config.environment.value)
    if config.debug:
        logger.debug("Debug mode enabled")

    widget_ref: dict[str, Optional[TickTockWidget]] = {"widget": None}

    def _activate_existing_instance() -> None:
        widget = widget_ref["widget"]
        if widget is not None:
            widget.request_external_activate()

    guard = SingleInstance(on_activate=_activate_existing_instance)
    if not guard.acquire():
        guard.notify_existing()
        _show_already_running_dialog()
        logger.error("Tick-Tock is already running. Exiting.")
        return 1

    try:
        storage, recovery_status = Storage.open_or_recover_with_status(
            Storage.default_db_path()
        )
        warnings: list[str] = []
        # Backup the verified-good database before writing any new session data.
        max_backups = int(config.get_timer_setting("max_backup_files", 5))
        try:
            storage.backup(keep=max_backups)
        except OSError as exc:
            logger.warning("Startup backup failed: %s", exc)
            warnings.append(
                "Could not create a startup backup. The app will continue, "
                "but recovery options may be reduced for this session."
            )
        retention_days = int(
            config.get_timer_setting("activity_history_retention_days", 3650)
        )
        retention_deleted = storage.apply_retention_policy(
            history_days=retention_days,
        )
        if any(v > 0 for v in retention_deleted.values()):
            logger.info("Retention policy pruned rows: %s", retention_deleted)

        if config.load_error:
            warnings.append(
                f"Config file is invalid \u2014 using default settings.\n"
                f"Error: {config.load_error}"
            )
        if recovery_status == RecoveryStatus.RECOVERED_FROM_BACKUP:
            warnings.append(
                "The primary database was corrupted and has been recovered from"
                " backup.\nSome recent activity may have been lost."
            )
        elif recovery_status == RecoveryStatus.FRESH_DB_CREATED:
            warnings.append(
                "The database could not be recovered from primary or backup.\n"
                "A fresh empty database was created (previous data is unavailable)."
            )

        startup_warning: Optional[str] = "\n\n".join(warnings) if warnings else None
        project_manager = ProjectManager(storage)
        app_service = AppService(
            storage=storage,
            project_manager=project_manager,
            default_backup_keep=max_backups,
        )
        widget = TickTockWidget(
            app_service=app_service,
            startup_warning=startup_warning,
            config=config,
        )
        widget_ref["widget"] = widget
        widget.run()
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Unhandled fatal exception in main")
        _show_fatal_crash_dialog(exc, log_path)
        return 2
    finally:
        guard.release()

    return 0


if __name__ == "__main__":
    sys.exit(main())
