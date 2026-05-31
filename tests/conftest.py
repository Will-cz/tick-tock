"""Shared test fixtures for Tick-Tock Widget test suite."""

import json
import os
import sys
import tkinter as tk
from tkinter import ttk
from pathlib import Path

import pytest

from src.config import Config
from src.timer import Timer

# ---------------------------------------------------------------------------
# Tk runtime bootstrap (Windows)
# ---------------------------------------------------------------------------


def _can_init_tk_with_ttk() -> bool:
    """Return True when both Tk and ttk theme discovery can initialize."""
    probe: tk.Tk | None = None
    try:
        probe = tk.Tk()
        probe.withdraw()
        style = ttk.Style(probe)
        _ = style.theme_names()
        return True
    except tk.TclError:
        return False
    finally:
        if probe is not None:
            try:
                probe.destroy()
            except tk.TclError:
                pass


def _ensure_tk_paths() -> None:
    """Stabilize Tk discovery when Tk/ttk cannot initialize by default."""

    # Prefer interpreter defaults when both Tk and ttk work.
    if _can_init_tk_with_ttk():
        return

    base = Path(sys.base_prefix)
    tcl_lib = base / "tcl" / "tcl8.6"
    tk_lib = base / "tcl" / "tk8.6"
    if tcl_lib.exists() and "TCL_LIBRARY" not in os.environ:
        os.environ["TCL_LIBRARY"] = str(tcl_lib)
    if tk_lib.exists() and "TK_LIBRARY" not in os.environ:
        os.environ["TK_LIBRARY"] = str(tk_lib)

    # Re-probe once so downstream fixtures observe the stabilized setup.
    _can_init_tk_with_ttk()


_ensure_tk_paths()


# ---------------------------------------------------------------------------
# Config fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def config_path(tmp_path: Path) -> Path:
    """Isolated config file path for each test."""
    return tmp_path / "config.json"


@pytest.fixture
def default_config(config_path: Path) -> Config:
    """Config instance using all defaults, isolated in a temp directory."""
    return Config(config_path=config_path)


@pytest.fixture
def dev_config(config_path: Path) -> Config:
    """Config instance pre-configured for the dev environment."""
    config_path.write_text(json.dumps({"environment": "dev"}))
    return Config(config_path=config_path)


# ---------------------------------------------------------------------------
# Timer fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def timer() -> Timer:
    """Fresh idle Timer instance."""
    return Timer()


@pytest.fixture
def running_timer():
    """Timer that has been started; guaranteed to be stopped after the test."""
    t = Timer()
    t.start()
    yield t
    t.stop()


# ---------------------------------------------------------------------------
# Mocking helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_open_error(mocker):
    """Patch builtins.open to raise OSError, simulating an unreadable file."""
    return mocker.patch("builtins.open", side_effect=OSError("mocked I/O error"))


@pytest.fixture
def isolated_env(monkeypatch: pytest.MonkeyPatch):
    """Remove TICK_TOCK_* env vars so the system environment cannot affect tests."""
    monkeypatch.delenv("TICK_TOCK_ENV", raising=False)
    monkeypatch.delenv("TICK_TOCK_DEBUG", raising=False)
