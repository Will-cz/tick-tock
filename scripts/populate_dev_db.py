"""Populate the dev database with realistic dummy data for the past ~3 months.

Use this to manually verify UI behavior such as the "Total Today" label.

The script is idempotent in the sense that it always recreates the dev DB
from scratch (deleting the existing file) before inserting fresh data.
"""

from __future__ import annotations

import random
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from src.paths import repo_data_dir
from src.storage import Storage


# Deterministic output across runs for easier comparison.
random.seed(20260531)

# Realistic ~8h workday split across projects. Per-project daily ranges are
# tuned so that on a typical weekday the total across all active projects
# lands in the 6-10h range and rarely exceeds 12h.
PROJECTS: list[dict[str, Any]] = [
    {
        "name": "Client Alpha",
        "description": "Long-running client engagement",
        "ref_number": "CA-001",
        "alias": "alpha",
        "color": "#1f77b4",
        "notes": "Weekly standup Mondays",
        "sub_activities": ["Design", "Build", "Review"],
        # Probability of doing any work on a random day.
        "work_density": 0.7,
        # Daily work range in minutes when active (~1-4h).
        "min_minutes": 60,
        "max_minutes": 240,
    },
    {
        "name": "Internal R&D",
        "description": "Prototype + experiments",
        "ref_number": "RD-014",
        "alias": "rnd",
        "color": "#2ca02c",
        "notes": "20% time",
        "sub_activities": ["Reading", "Prototyping"],
        "work_density": 0.35,
        # ~20min-1.5h.
        "min_minutes": 20,
        "max_minutes": 90,
    },
    {
        "name": "Admin",
        "description": "Email, planning, misc.",
        "ref_number": "ADM",
        "alias": "admin",
        "color": "#ff7f0e",
        "notes": "",
        "sub_activities": [],
        "work_density": 0.9,
        # ~5-30min.
        "min_minutes": 5,
        "max_minutes": 30,
    },
    {
        "name": "Side Project",
        "description": "Weekend coding",
        "ref_number": "",
        "alias": "side",
        "color": "#9467bd",
        "notes": "Open source",
        "sub_activities": ["Coding", "Docs"],
        "work_density": 0.25,
        # ~30min-2h.
        "min_minutes": 30,
        "max_minutes": 120,
    },
]

# Hard cap on combined daily minutes across all projects (keeps a day under
# ~10h even if random draws all skew high).
MAX_DAILY_TOTAL_MINUTES = 10 * 60


def populate(db_path: Path, *, history_days: int = 90) -> None:
    if db_path.exists():
        db_path.unlink()
    for suffix in ("-wal", "-shm"):
        sidecar = db_path.with_name(db_path.name + suffix)
        if sidecar.exists():
            sidecar.unlink()

    storage = Storage(db_path)
    today = date.today()
    start_day = today - timedelta(days=history_days)

    # Replace the auto-created default project's metadata or create new
    # projects fresh. Easiest: just create new projects; the default empty one
    # remains harmlessly.
    project_records: list[tuple[int, dict[str, Any]]] = []
    for proj_cfg in PROJECTS:
        project_id = storage.create_project(
            str(proj_cfg["name"]),
            str(proj_cfg["description"]),
            ref_number=str(proj_cfg.get("ref_number", "")),
            alias=str(proj_cfg.get("alias", "")),
            color=str(proj_cfg.get("color", "")),
            notes=str(proj_cfg.get("notes", "")),
        )
        project_records.append((project_id, proj_cfg))

    # Create sub-activities per project.
    sub_records: dict[int, list[int]] = {}
    for project_id, cfg in project_records:
        sub_ids: list[int] = []
        for sub_name in cfg.get("sub_activities", []):
            sub_ids.append(storage.create_sub_activity(project_id, str(sub_name)))
        sub_records[project_id] = sub_ids

    # Walk each day and add daily totals + sub-activity splits.
    project_lifetime: dict[int, float] = {pid: 0.0 for pid, _ in project_records}
    sub_lifetime: dict[int, float] = {}

    for offset in range(history_days + 1):  # include today
        day = start_day + timedelta(days=offset)
        day_str = day.isoformat()
        force_activity = day == today  # guarantee today has data for all projects
        day_minutes_used = 0

        for project_id, cfg in project_records:
            density = float(cfg["work_density"])
            # Weekend dampening: less likely to work weekends, except Side Project.
            is_weekend = day.weekday() >= 5
            effective_density = density
            if is_weekend and cfg["name"] != "Side Project":
                effective_density *= 0.25
            if not force_activity and random.random() > effective_density:
                continue

            minutes = random.randint(
                int(cfg["min_minutes"]),
                int(cfg["max_minutes"]),
            )
            # Enforce realistic daily cap across all projects.
            remaining = MAX_DAILY_TOTAL_MINUTES - day_minutes_used
            if remaining <= 0:
                continue
            minutes = min(minutes, remaining)
            day_minutes_used += minutes
            seconds = float(minutes * 60)
            storage.add_daily_seconds(project_id, day_str, seconds)
            project_lifetime[project_id] += seconds

            sub_ids = sub_records.get(project_id, [])
            if sub_ids:
                # Of the day's project seconds, a random fraction goes to
                # sub-activities; the remainder is "no-activity" time that
                # contributes only to the project daily total. This mirrors
                # real runtime behaviour where time accrues to the project
                # even when no sub-activity is selected.
                sub_fraction = random.uniform(0.4, 0.9)
                sub_total_seconds = round(seconds * sub_fraction)
                # Distribute the sub-activity seconds across sub-activities (uneven).
                weights = [random.random() + 0.1 for _ in sub_ids]
                total_w = sum(weights)
                remaining_sub = sub_total_seconds
                for idx, sub_id in enumerate(sub_ids):
                    if idx == len(sub_ids) - 1:
                        portion = remaining_sub
                    else:
                        portion = round(sub_total_seconds * weights[idx] / total_w)
                        portion = min(portion, remaining_sub)
                        remaining_sub -= portion
                    if portion <= 0:
                        continue
                    storage.add_daily_sub_activity_seconds(
                        project_id, sub_id, day_str, float(portion)
                    )
                    sub_lifetime[sub_id] = sub_lifetime.get(sub_id, 0.0) + float(
                        portion
                    )

    # Persist lifetime totals onto projects and sub-activities.
    for project_id, _cfg in project_records:
        storage.save_project_elapsed(project_id, project_lifetime[project_id])
    for sub_id, total in sub_lifetime.items():
        storage.save_sub_activity_elapsed(sub_id, total)

    # Make the first real project the active one.
    first_project_id = project_records[0][0]
    storage.set_app_state("active_project_id", str(first_project_id))

    # Optional: seed a STOPPED timer state at lifetime so the play button
    # exercises the "continue_from_stopped" path, which is where the
    # today-vs-lifetime bug class tends to surface.
    storage.save_timer_state(project_lifetime[first_project_id], "stopped")

    # Summary printout.
    print(f"DB written: {db_path}")
    print(f"Date range: {start_day} .. {today} ({history_days + 1} days)")
    print("Projects:")
    for project_id, cfg in project_records:
        hours = project_lifetime[project_id] / 3600.0
        print(f"  [{project_id:>2}] {cfg['name']!s:<14}" f"  lifetime ≈ {hours:6.1f} h")
    today_total = storage.get_daily_total(today.isoformat())
    print(
        f"Today ({today.isoformat()}) total across all projects: "
        f"{today_total / 3600.0:.2f} h"
    )
    today_by_project = storage.get_daily_seconds_by_project(today.isoformat())
    for project_id, secs in sorted(today_by_project.items()):
        print(f"  project {project_id}: today = {secs / 3600.0:.2f} h")


def main() -> None:
    db_path = repo_data_dir() / "tick_tock.dev.db"
    print(f"Populating {db_path} with last 90 days of dummy data...")
    populate(db_path, history_days=90)
    print(f"Generated at {datetime.now().isoformat(timespec='seconds')}")


if __name__ == "__main__":
    main()
