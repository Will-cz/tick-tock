from __future__ import annotations

import calendar
from datetime import date

import pytest

from src.storage import Storage
from src.ui.dialogs.report_payload import compute_refresh_payload


def _project_payload(project_id: int, name: str) -> dict[str, object]:
    return {
        "project_id": project_id,
        "name": name,
        "alias": "",
    }


def test_compute_refresh_payload_monthly_handles_large_project_matrix(
    tmp_path,
) -> None:
    storage = Storage(tmp_path / "report_payload_large_monthly.db")

    year = 2026
    month = 3
    days_in_month = calendar.monthrange(year, month)[1]
    project_ids = [storage.create_project(f"P-{idx}", "") for idx in range(12)]

    for day in range(1, days_in_month + 1):
        day_text = date(year, month, day).isoformat()
        for project_idx, project_id in enumerate(project_ids):
            storage.add_daily_seconds(
                project_id,
                day_text,
                float(project_idx + day),
            )

    # Add out-of-month data to verify monthly slicing ignores it.
    storage.add_daily_seconds(project_ids[0], "2025-03-10", 9999.0)

    request = {
        "mode": "monthly",
        "year": year,
        "month": month,
        "week_start": date(year, month, 1),
        "projects": [
            _project_payload(project_id, f"P-{idx}")
            for idx, project_id in enumerate(project_ids)
        ],
        "live_project_id": None,
        "live_delta": 0.0,
    }

    payload = compute_refresh_payload(storage, request)

    assert payload["mode"] == "monthly"
    assert payload["rows_total"] == 12
    assert len(payload["rows"]) == 12
    assert len(payload["day_cols"]) == days_in_month

    expected_grand_total = 0.0
    for project_idx in range(12):
        expected_grand_total += sum(
            float(project_idx + day) for day in range(1, days_in_month + 1)
        )

    assert payload["totals"]["total"] == pytest.approx(expected_grand_total)

    sample_row = payload["rows"][5]
    expected_sample_total = sum(float(5 + day) for day in range(1, days_in_month + 1))
    assert sample_row["total"] == pytest.approx(expected_sample_total)


def test_compute_refresh_payload_weekly_handles_cross_year_range(tmp_path) -> None:
    storage = Storage(tmp_path / "report_payload_week_cross_year.db")
    project_id = storage.create_project("CrossYear", "")

    storage.add_daily_seconds(project_id, "2025-12-31", 1200.0)
    storage.add_daily_seconds(project_id, "2026-01-01", 2400.0)

    week_start = date(2025, 12, 29)  # Mon -> spans into Jan 2026
    request = {
        "mode": "weekly",
        "year": 2025,
        "month": 12,
        "week_start": week_start,
        "projects": [_project_payload(project_id, "CrossYear")],
        "live_project_id": None,
        "live_delta": 0.0,
    }

    payload = compute_refresh_payload(storage, request)

    assert payload["mode"] == "weekly"
    assert len(payload["rows"]) == 1
    row = payload["rows"][0]

    # week_start + 2 => 2025-12-31, week_start + 3 => 2026-01-01
    assert row["d2"] == pytest.approx(1200.0)
    assert row["d3"] == pytest.approx(2400.0)
    assert row["total"] == pytest.approx(3600.0)


def test_compute_refresh_payload_monthly_handles_many_sub_activity_rows(
    tmp_path,
) -> None:
    storage = Storage(tmp_path / "report_payload_many_subs.db")
    project_id = storage.create_project("Main", "")

    year = 2026
    month = 4
    day_text = date(year, month, 3).isoformat()

    total_project_seconds = 0.0
    for idx in range(120):
        sub_id = storage.create_sub_activity(project_id, f"S-{idx}")
        seconds = float(idx + 1)
        storage.add_daily_sub_activity_seconds(project_id, sub_id, day_text, seconds)
        total_project_seconds += seconds

    storage.add_daily_seconds(project_id, day_text, total_project_seconds)

    request = {
        "mode": "monthly",
        "year": year,
        "month": month,
        "week_start": date(year, month, 1),
        "projects": [_project_payload(project_id, "Main")],
        "live_project_id": None,
        "live_delta": 0.0,
    }

    payload = compute_refresh_payload(storage, request)

    assert payload["rows_total"] == 1
    row = payload["rows"][0]
    assert row["total"] == pytest.approx(total_project_seconds)
    assert len(row["children"]) == 120
    assert sum(float(child["total"]) for child in row["children"]) == pytest.approx(
        total_project_seconds
    )


def test_compute_refresh_payload_monthly_applies_live_delta_to_sub_activity(tmp_path):
    storage = Storage(tmp_path / "report_payload_live_sub.db")
    project_id = storage.create_project("Live", "")
    sub_id = storage.create_sub_activity(project_id, "Live Sub")

    today = date.today()
    storage.add_daily_seconds(project_id, today.isoformat(), 120.0)
    storage.add_daily_sub_activity_seconds(project_id, sub_id, today.isoformat(), 120.0)

    request = {
        "mode": "monthly",
        "year": today.year,
        "month": today.month,
        "week_start": today.replace(day=1),
        "projects": [_project_payload(project_id, "Live")],
        "live_project_id": project_id,
        "live_sub_activity_id": sub_id,
        "live_delta": 30.0,
    }

    payload = compute_refresh_payload(storage, request)

    row = payload["rows"][0]
    assert row["total"] == pytest.approx(150.0)
    child = next(c for c in row["children"] if c["name"] == "Live Sub")
    assert child["total"] == pytest.approx(150.0)
