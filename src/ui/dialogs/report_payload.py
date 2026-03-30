"""Background payload builder for report dialog refreshes."""

from __future__ import annotations

import calendar
from datetime import date, datetime, timedelta
from typing import Any

from src.storage import Storage

RowData = dict[str, object]


def _to_float(value: object) -> float:
    if not isinstance(value, (int, float, str, bytes, bytearray)):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _weekend_days(year: int, month: int) -> list[int]:
    num_days = calendar.monthrange(year, month)[1]
    return [d for d in range(1, num_days + 1) if date(year, month, d).weekday() >= 5]


def compute_refresh_payload(
    storage: Storage, request: dict[str, Any]
) -> dict[str, Any]:
    """Build report table payload for monthly or weekly mode."""
    mode = str(request.get("mode", "monthly"))
    projects = request.get("projects", [])
    project_ids = [int(p["project_id"]) for p in projects]
    live_project_id = request.get("live_project_id")
    live_sub_activity_id = request.get("live_sub_activity_id")
    live_delta = float(request.get("live_delta", 0.0))

    if mode == "monthly":
        year = int(request["year"])
        month = int(request["month"])
        num_days = calendar.monthrange(year, month)[1]
        weekend_days = _weekend_days(year, month)
        day_cols = [f"d{d}" for d in range(1, num_days + 1)]
        monthly = storage.get_monthly_data(year, month, project_ids=project_ids)
        monthly_sub = storage.get_monthly_sub_activity_data(
            year, month, project_ids=project_ids
        )
        if (
            live_project_id is not None
            and live_delta > 0
            and year == datetime.now().year
            and month == datetime.now().month
            and (not project_ids or int(live_project_id) in project_ids)
        ):
            today_str = date.today().isoformat()
            monthly.setdefault(int(live_project_id), {})[today_str] = (
                monthly.get(int(live_project_id), {}).get(today_str, 0.0) + live_delta
            )
            if live_sub_activity_id is not None:
                sub_id = int(live_sub_activity_id)
                project_bucket = monthly_sub.setdefault(int(live_project_id), {})
                sub_bucket = project_bucket.setdefault(sub_id, {})
                sub_bucket[today_str] = sub_bucket.get(today_str, 0.0) + live_delta

        rows: list[RowData] = []
        daily_totals: dict[str, float] = {col: 0.0 for col in day_cols}
        grand_total = 0.0
        for proj in projects:
            project_id = int(proj["project_id"])
            row: RowData = {"name": (proj.get("alias") or proj.get("name") or "")}
            proj_total = 0.0
            for day in range(1, num_days + 1):
                row[f"d{day}"] = 0.0
            for date_str, secs in monthly.get(project_id, {}).items():
                try:
                    day = date.fromisoformat(date_str).day
                except ValueError:
                    continue
                if not 1 <= day <= num_days:
                    continue
                key = f"d{day}"
                row[key] = _to_float(row.get(key, 0.0)) + secs
                daily_totals[key] += secs
                proj_total += secs
                grand_total += secs
            row["total"] = proj_total

            children: list[RowData] = []
            for sub in storage.list_sub_activities(project_id):
                if sub.get("archived"):
                    continue
                child: RowData = {"name": str(sub.get("name", ""))}
                for key in day_cols:
                    child[key] = 0.0
                sub_map = monthly_sub.get(project_id, {}).get(int(sub.get("id", 0)), {})
                sub_total = 0.0
                for date_str, secs in sub_map.items():
                    try:
                        day = date.fromisoformat(date_str).day
                    except ValueError:
                        continue
                    if not 1 <= day <= num_days:
                        continue
                    key = f"d{day}"
                    child[key] = _to_float(child.get(key, 0.0)) + secs
                    sub_total += secs
                child["total"] = sub_total
                children.append(child)
            row["children"] = children
            rows.append(row)

        return {
            "mode": "monthly",
            "columns": day_cols + ["total"],
            "day_cols": day_cols,
            "weekend_days": weekend_days,
            "rows": rows,
            "totals": {**daily_totals, "total": grand_total},
            "range_text": f"{calendar.month_name[month]} {year}",
            "rows_total": len(projects),
        }

    week_start: date = request["week_start"]
    week_dates = [week_start + timedelta(days=i) for i in range(7)]
    day_cols = [f"d{i}" for i in range(7)]
    weekly = storage.get_date_range_data(
        week_dates[0], week_dates[6], project_ids=project_ids
    )
    weekly_sub = storage.get_date_range_sub_activity_data(
        week_dates[0], week_dates[6], project_ids=project_ids
    )
    if live_project_id is not None and live_delta > 0:
        today = date.today()
        if week_dates[0] <= today <= week_dates[6] and (
            not project_ids or int(live_project_id) in project_ids
        ):
            today_str = today.isoformat()
            weekly.setdefault(int(live_project_id), {})[today_str] = (
                weekly.get(int(live_project_id), {}).get(today_str, 0.0) + live_delta
            )
            if live_sub_activity_id is not None:
                sub_id = int(live_sub_activity_id)
                project_bucket = weekly_sub.setdefault(int(live_project_id), {})
                sub_bucket = project_bucket.setdefault(sub_id, {})
                sub_bucket[today_str] = sub_bucket.get(today_str, 0.0) + live_delta

    rows_w: list[RowData] = []
    day_totals_w: dict[str, float] = {col: 0.0 for col in day_cols}
    grand_total_w = 0.0
    for proj in projects:
        project_id = int(proj["project_id"])
        row_w: RowData = {"name": (proj.get("alias") or proj.get("name") or "")}
        proj_total = 0.0
        for col in day_cols:
            row_w[col] = 0.0
        for date_str, secs in weekly.get(project_id, {}).items():
            try:
                current = date.fromisoformat(date_str)
            except ValueError:
                continue
            idx = (current - week_dates[0]).days
            if not 0 <= idx < 7:
                continue
            col = f"d{idx}"
            row_w[col] = _to_float(row_w.get(col, 0.0)) + secs
            day_totals_w[col] += secs
            proj_total += secs
            grand_total_w += secs
        row_w["total"] = proj_total

        children_w: list[RowData] = []
        for sub in storage.list_sub_activities(project_id):
            if sub.get("archived"):
                continue
            child_w: RowData = {"name": str(sub.get("name", ""))}
            for key in day_cols:
                child_w[key] = 0.0
            sub_map = weekly_sub.get(project_id, {}).get(int(sub.get("id", 0)), {})
            sub_total = 0.0
            for date_str, secs in sub_map.items():
                try:
                    current = date.fromisoformat(date_str)
                except ValueError:
                    continue
                idx = (current - week_dates[0]).days
                if not 0 <= idx < 7:
                    continue
                key = f"d{idx}"
                child_w[key] = _to_float(child_w.get(key, 0.0)) + secs
                sub_total += secs
            child_w["total"] = sub_total
            children_w.append(child_w)
        row_w["children"] = children_w
        rows_w.append(row_w)

    end = week_start + timedelta(days=6)
    week_label = (
        f"{week_start.strftime('%b %d')}-{end.day}, {end.year}"
        if week_start.month == end.month
        else f"{week_start.strftime('%b %d')} - {end.strftime('%b %d, %Y')}"
    )
    return {
        "mode": "weekly",
        "columns": day_cols + ["total"],
        "day_cols": day_cols,
        "rows": rows_w,
        "totals": {**day_totals_w, "total": grand_total_w},
        "range_text": week_label,
        "rows_total": len(projects),
    }
