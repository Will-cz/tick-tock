"""Bootstrap the dev DB and dump its schema for verification."""

from __future__ import annotations

import sqlite3

from src.paths import repo_data_dir
from src.storage import Storage


def main() -> None:
    path = repo_data_dir() / "tick_tock.dev.db"
    Storage(path)
    conn = sqlite3.connect(path)
    try:
        tables = sorted(
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        )
        versions = sorted(
            row[0] for row in conn.execute("SELECT version FROM schema_migrations")
        )
        indexes = sorted(
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND sql IS NOT NULL"
            )
        )
        print("tables:", tables)
        print("schema versions:", versions)
        print("indexes:", indexes)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
