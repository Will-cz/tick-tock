#!/usr/bin/env python3
"""
Tick-Tock Widget - Development launcher

Usage:
    python run.py              # prod (default)
    python run.py dev          # dev mode + debug logging
    python run.py test         # test environment
    python run.py prototype    # prototype environment
"""

import os
import sys
from pathlib import Path

# Map friendly shorthand → TICK_TOCK_ENV value
_MODES = {
    "dev": "dev",
    "development": "dev",
    "test": "test",
    "prototype": "prototype",
    "prod": "prod",
    "production": "prod",
}


def _resolve_mode_arg(argv: list[str]) -> str:
    """Resolve launch mode from CLI arg, then bundled default, then prod."""
    if len(argv) > 1:
        return argv[1].lower()
    # Packaged builds can inject this via a PyInstaller runtime hook.
    return os.environ.get("TICK_TOCK_DEFAULT_ENV", "prod").lower()


if __name__ == "__main__":
    mode_arg = _resolve_mode_arg(sys.argv)
    env = _MODES.get(mode_arg)
    if env is None:
        print(f"Unknown mode '{mode_arg}'. Choose from: {', '.join(_MODES)}")
        sys.exit(1)

    os.environ["TICK_TOCK_ENV"] = env
    if env == "dev":
        os.environ.setdefault("TICK_TOCK_DEBUG", "1")

    print(f"Starting Tick-Tock Widget [{env.upper()}]")

    # Put project root on path so package imports resolve in local runs.
    sys.path.insert(0, str(Path(__file__).parent))

    from src.main import main  # noqa: E402

    sys.exit(main())
