#!/usr/bin/env python3
"""
Tick-Tock Widget - Build launcher

Usage:
    python build.py                   # clean build (default)
    python build.py fast              # skip PyInstaller clean step
    python build.py deps              # install build dependencies first
    python build.py deps fast         # install deps + skip clean
    python build.py --python-exe PATH # use a specific Python interpreter
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

_FLAGS = {
    "deps": "install_deps",
    "install-deps": "install_deps",
    "install": "install_deps",
    "fast": "skip_clean",
    "skip-clean": "skip_clean",
    "clean": "clean",
}


def _print_usage() -> None:
    print(__doc__.strip())


def _resolve_paths() -> tuple[Path, Path]:
    project_root = Path(__file__).resolve().parent
    build_script = project_root / "scripts" / "build_exe.ps1"
    if not build_script.exists():
        print(f"Build script not found at: {build_script}")
        sys.exit(1)
    return project_root, build_script


def _resolve_powershell_exe() -> str:
    for candidate in ("powershell", "pwsh"):
        if shutil.which(candidate):
            return candidate

    print("PowerShell executable was not found (tried: powershell, pwsh).")
    sys.exit(1)


def _parse_args(argv: list[str]) -> tuple[bool, bool, str | None]:
    install_deps = False
    skip_clean = False
    python_exe: str | None = None

    i = 1
    while i < len(argv):
        raw_arg = argv[i]
        arg = raw_arg.lower()

        if arg in {"-h", "--help"}:
            _print_usage()
            sys.exit(0)

        if arg in {"--python-exe", "--python"}:
            if i + 1 >= len(argv):
                print("Missing value for --python-exe")
                sys.exit(1)
            python_exe = argv[i + 1]
            i += 2
            continue

        flag = _FLAGS.get(arg)
        if flag is None:
            print(f"Unknown build option '{raw_arg}'.")
            _print_usage()
            sys.exit(1)

        if flag == "install_deps":
            install_deps = True
        elif flag == "skip_clean":
            skip_clean = True
        elif flag == "clean":
            skip_clean = False

        i += 1

    return install_deps, skip_clean, python_exe


def main() -> int:
    install_deps, skip_clean, python_exe = _parse_args(sys.argv)
    project_root, build_script = _resolve_paths()
    powershell_exe = _resolve_powershell_exe()

    cmd: list[str] = [
        powershell_exe,
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(build_script),
    ]

    if python_exe:
        cmd += ["-PythonExe", python_exe]
    if install_deps:
        cmd.append("-InstallBuildDeps")
    if skip_clean:
        cmd.append("-SkipClean")

    print("Building Tick-Tock EXE...")
    if install_deps:
        print("- Installing build dependencies")
    if skip_clean:
        print("- Skip clean enabled")

    completed = subprocess.run(cmd, cwd=project_root, check=False)
    return completed.returncode


if __name__ == "__main__":
    sys.exit(main())
