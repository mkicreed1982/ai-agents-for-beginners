"""Sandbox setup tool for the AI Agents for Beginners course.

This application:
  1. Creates an isolated Python virtual environment (the "sandbox").
  2. Installs the course dependencies (requirements.txt) into it.
  3. Writes an empty-template ``.env`` file inside the sandbox so the
     learner can fill in their own secrets.

It is designed to run either as a plain Python script or as a standalone
Windows ``.exe`` produced by PyInstaller (see build_exe.py). For that reason
it only relies on the Python standard library.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import venv
from pathlib import Path

# Keys used by the course, in case .env.example cannot be located (e.g. when the
# .exe is run from an arbitrary folder). Kept in sync with .env.example.
FALLBACK_ENV_TEMPLATE = """\
# Azure AI Foundry Project (Required for most lessons)
AZURE_AI_PROJECT_ENDPOINT=""
AZURE_AI_MODEL_DEPLOYMENT_NAME=""

# Azure AI Search (Required for Lesson 05 - Agentic RAG)
AZURE_SEARCH_SERVICE_ENDPOINT=""
AZURE_SEARCH_API_KEY=""

# GitHub Models (Required for Lesson 06 and Lesson 08 GitHub Models workflows)
GITHUB_TOKEN=""
GITHUB_ENDPOINT=""
GITHUB_MODEL_ID=""

# Azure AI Bing Connection (Required for Lesson 08 - Bing grounding workflow)
BING_CONNECTION_ID=""

# MiniMax (Alternative OpenAI-compatible provider)
MINIMAX_API_KEY=""
MINIMAX_BASE_URL=""
MINIMAX_MODEL_ID=""
"""

# Matches an environment assignment line such as KEY="value" or KEY=value.
_ASSIGNMENT_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=")


def find_repo_root(start: Path) -> Path | None:
    """Walk upwards from *start* looking for the course repo root.

    The repo root is identified by the presence of requirements.txt. Returns
    None if not found (e.g. the .exe was copied somewhere unrelated).
    """
    for candidate in [start, *start.parents]:
        if (candidate / "requirements.txt").is_file():
            return candidate
    return None


def build_env_template(example_path: Path | None) -> str:
    """Produce an empty-template .env body.

    If *example_path* exists, comment lines are preserved and every assignment
    is blanked out (KEY=""). Otherwise the built-in fallback template is used.
    """
    if example_path is None or not example_path.is_file():
        return FALLBACK_ENV_TEMPLATE

    out_lines: list[str] = []
    for raw in example_path.read_text(encoding="utf-8").splitlines():
        match = _ASSIGNMENT_RE.match(raw)
        if match and not raw.lstrip().startswith("#"):
            out_lines.append(f'{match.group(1)}=""')
        else:
            # Preserve comments and blank lines for readability.
            out_lines.append(raw)
    return "\n".join(out_lines).rstrip() + "\n"


def venv_python(venv_dir: Path) -> Path:
    """Return the python executable inside a venv for the current platform."""
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def create_venv(venv_dir: Path) -> None:
    print(f"[1/3] Creating virtual environment at: {venv_dir}")
    builder = venv.EnvBuilder(with_pip=True, clear=False, upgrade_deps=False)
    builder.create(str(venv_dir))


def install_requirements(venv_dir: Path, requirements: Path | None) -> None:
    if requirements is None or not requirements.is_file():
        print("[2/3] No requirements.txt found - skipping dependency install.")
        return
    python = venv_python(venv_dir)
    print(f"[2/3] Installing dependencies from: {requirements}")
    subprocess.run(
        [str(python), "-m", "pip", "install", "--upgrade", "pip"],
        check=True,
    )
    subprocess.run(
        [str(python), "-m", "pip", "install", "-r", str(requirements)],
        check=True,
    )


def write_env_file(env_path: Path, example_path: Path | None, force: bool) -> None:
    print(f"[3/3] Writing environment file: {env_path}")
    if env_path.exists() and not force:
        print(f"      .env already exists - leaving it untouched (use --force to overwrite).")
        return
    env_path.write_text(build_env_template(example_path), encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="sandbox-setup",
        description=(
            "Create a Python virtual-env sandbox for the AI Agents for "
            "Beginners course and drop an empty .env template inside it."
        ),
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Directory in which to create the sandbox (default: current directory).",
    )
    parser.add_argument(
        "--name",
        default="sandbox",
        help="Name of the sandbox folder to create (default: sandbox).",
    )
    parser.add_argument(
        "--requirements",
        default=None,
        help="Path to a requirements.txt to install (default: auto-detect from repo root).",
    )
    parser.add_argument(
        "--no-install",
        action="store_true",
        help="Create the venv and .env but skip installing dependencies.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing .env file inside the sandbox.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)

    target = Path(args.target).expanduser().resolve()
    sandbox_dir = target / args.name
    venv_dir = sandbox_dir / ".venv"
    env_path = sandbox_dir / ".env"

    # Locate the repo so we can find requirements.txt and .env.example.
    repo_root = find_repo_root(Path.cwd())
    if args.requirements:
        requirements = Path(args.requirements).expanduser().resolve()
    elif repo_root is not None:
        requirements = repo_root / "requirements.txt"
    else:
        requirements = None

    example_path = (repo_root / ".env.example") if repo_root is not None else None

    print("=" * 60)
    print(" AI Agents for Beginners - Sandbox Setup")
    print("=" * 60)
    print(f"Sandbox location : {sandbox_dir}")
    if repo_root is not None:
        print(f"Course repo root : {repo_root}")
    print("-" * 60)

    sandbox_dir.mkdir(parents=True, exist_ok=True)

    try:
        create_venv(venv_dir)
        if args.no_install:
            print("[2/3] Skipping dependency install (--no-install).")
        else:
            install_requirements(venv_dir, requirements)
        write_env_file(env_path, example_path, args.force)
    except subprocess.CalledProcessError as exc:
        print(f"\nERROR: a setup command failed (exit code {exc.returncode}).", file=sys.stderr)
        return exc.returncode
    except OSError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        return 1

    activate = (
        venv_dir / ("Scripts/activate" if os.name == "nt" else "bin/activate")
    )
    print("-" * 60)
    print("Done! Your sandbox is ready.")
    print(f"  Activate it with:\n    {activate}")
    print(f"  Then edit your secrets in:\n    {env_path}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
