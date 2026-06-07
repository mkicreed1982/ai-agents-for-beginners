"""Build a standalone Windows .exe from sandbox_setup.py using PyInstaller.

Usage:
    pip install pyinstaller
    python build_exe.py

The resulting executable is written to ``dist/sandbox-setup.exe``.

This script works on any platform PyInstaller supports, but to produce a
Windows ``.exe`` you must run it on Windows (PyInstaller does not
cross-compile).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENTRY = HERE / "sandbox_setup.py"
APP_NAME = "sandbox-setup"


def main() -> int:
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print(
            "PyInstaller is not installed. Install it first:\n"
            "    pip install pyinstaller",
            file=sys.stderr,
        )
        return 1

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--console",
        "--name",
        APP_NAME,
        "--distpath",
        str(HERE / "dist"),
        "--workpath",
        str(HERE / "build"),
        "--specpath",
        str(HERE),
        str(ENTRY),
    ]
    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd)
    if result.returncode == 0:
        exe = HERE / "dist" / (APP_NAME + (".exe" if sys.platform == "win32" else ""))
        print(f"\nBuilt: {exe}")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
