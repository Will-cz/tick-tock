"""User-data directory helper for Tick-Tock Widget.

All mutable data (database, config, backups) is stored in an OS-appropriate
per-user writable location. This policy is used for both frozen and non-frozen
launches so source installs do not write into installation-adjacent paths.
"""

import os
from pathlib import Path


def user_data_dir() -> Path:
    """Return the directory where user data files should be stored.

    Rules:
    - Use ``%LOCALAPPDATA%\\TickTock`` when LOCALAPPDATA is available.
    - Fall back to ``~/.tick-tock`` when LOCALAPPDATA is not set.
    """
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "TickTock"
    return Path.home() / ".tick-tock"
