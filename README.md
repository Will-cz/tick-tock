# Tick-Tock Widget

Personal time tracking desktop application for Windows.

## Overview

Tick-Tock is a lightweight timer widget designed for daily personal project tracking. It combines a fast desktop UI with persistent local storage, per-project and sub-activity tracking, report export, backup/recovery safeguards, and a strong automated test suite.

## Core Features

- Always-on-top timer widget with start, pause, resume/continue, stop, and reset.
- Project management with metadata (alias, reference, color, notes) and archive controls.
- Sub-activity tracking within each project.
- Daily and historical time logging with report views.
- Import/export to JSON and automatic database backup with retention.
- System tray support (show/hide and quit).
- Runtime modes (`prod`, `dev`, `test`, `prototype`) with isolated config/database files.
- Config hot-reload and user preference persistence.

## Requirements

- Windows OS
- Python 3.9+

## Quick Start

1. Create and activate a virtual environment.

	PowerShell:
	```powershell
	py -3.9 -m venv .venv
	.\.venv\Scripts\Activate.ps1
	```

2. Install runtime dependencies.

	```powershell
	python -m pip install -r requirements.txt
	```

3. Launch the app.

	```powershell
	python run.py prod
	```

## Run Modes

`run.py` supports these modes:

- `prod` (default)
- `dev`
- `test`
- `prototype`

Examples:

```powershell
python run.py          # defaults to prod
python run.py dev
python run.py test
python run.py prototype
```

Environment behavior:

- `TICK_TOCK_ENV` controls runtime environment selection.
- `TICK_TOCK_DEFAULT_ENV` is used by packaged builds when no CLI arg is supplied.
- `TICK_TOCK_DEBUG=1` enables debug logging behavior.

## Data, Config, and Logs

Tick-Tock stores user data in a per-user writable location:

- Primary: `%LOCALAPPDATA%\TickTock`
- Fallback: `~/.tick-tock`

Mode-specific file names:

- Database:
  - `prod`: `tick_tock.db`
  - `dev/test/prototype`: `tick_tock.<env>.db`
- Config:
  - `prod`: `config.json`
  - `dev/test/prototype`: `config.<env>.json`
- Logs:
  - `logs/tick_tock.log` (rotating file logging)

Backups:

- Standard recovery backup: `<db>.bak`
- Timestamped backups: `<db>.backup.YYYYMMDD-HHMMSS-ffffff`

## Architecture Snapshot

- `run.py`: environment-aware launcher.
- `src/main.py`: app bootstrap, single-instance guard, startup recovery/backup flow.
- `src/ui/widget.py`: Tkinter UI shell and interaction wiring.
- `src/ui/widget_controller.py`: timer-event persistence coordinator (UI-free, testable).
- `src/app_service.py`: service boundary between UI and persistence.
- `src/app/services/*`: focused domain helpers for tree/session/report/import-export behavior.
- `src/storage.py` + `src/infra/persistence/*`: SQLite persistence, migrations, validation, and recovery.
- `src/config.py`: config load/sanitize/migrate/watch.

## Testing

Default pytest configuration includes coverage (minimum 80%) and test markers for multiple layers.

Common commands:

```powershell
python -m pytest -v
python -m pytest tests/unit/ -v
python -m pytest -q -m "not gui" --cov-fail-under=0
python -m pytest -q -m gui --cov-fail-under=0
```

VS Code tasks are provided:

- `Test: Unit`
- `Test: All`
- `Run: Prod`
- `Run: Dev`
- `Run: Test env`
- `Run: Prototype`

## Build Windows EXE

1. Install build dependencies:

	```powershell
	python -m pip install -r requirements-build.txt
	```

2. Build executable and delivery artifacts:

	```powershell
	python build.py
	```

	Equivalent direct script call:

	```powershell
	powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build_exe.ps1
	```

	Useful options with the wrapper:

	```powershell
	python build.py deps
	python build.py fast
	python build.py --python-exe .\.venv\Scripts\python.exe
	```

You can also run the VS Code task `Build: EXE`.

Build outputs:

- `dist/TickTock.exe`
- `dist/releases/TickTock-<version>-win64-<timestamp>.exe`
- `dist/releases/TickTock-v<version>-win64.exe`
- `dist/releases/TickTock-latest.exe`

Packaging note:

- Version `0.2.0` is currently packaged with a prototype default runtime mode for alpha delivery.
- Other versions default packaged runtime mode to `prod`.

## Development Notes

- System tray support requires `pystray` and `Pillow` (both listed in `requirements.txt`).
- The test harness includes Tk/ttk bootstrap logic in `tests/conftest.py` for improved Windows reliability.

## License

See [LICENSE](LICENSE) for details.

## Status

Active development. Core functionality is implemented and broadly covered by automated tests, with ongoing refinements to UX and feature depth.
