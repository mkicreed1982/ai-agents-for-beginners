# Sandbox Setup Tool

A small command-line app that bootstraps an isolated working environment for the
**AI Agents for Beginners** course. It:

1. **Creates a sandbox** — an isolated Python virtual environment (`.venv`).
2. **Installs dependencies** from the course `requirements.txt` into it.
3. **Writes an empty `.env` template** inside the sandbox so you can fill in your
   own keys (Azure AI Foundry, GitHub Models, etc.).

The keys in the generated `.env` are derived from the repo's
[`.env.example`](../../.env.example) (with all values blanked out), so it always
matches the lessons.

## Run as a Python script

From the repo root (or anywhere inside the repo):

```bash
python tools/sandbox-setup/sandbox_setup.py
```

This creates `./sandbox/` containing `.venv/` and an empty `.env`.

### Options

| Flag             | Description                                                        |
| ---------------- | ------------------------------------------------------------------ |
| `target`         | Directory to create the sandbox in (positional, default: `.`).     |
| `--name NAME`    | Sandbox folder name (default: `sandbox`).                          |
| `--requirements` | Path to a `requirements.txt` (default: auto-detected from repo).  |
| `--no-install`   | Create the venv and `.env` but skip `pip install`.                |
| `--force`        | Overwrite an existing `.env` inside the sandbox.                   |

Example:

```bash
python tools/sandbox-setup/sandbox_setup.py C:\work --name agents-lab --force
```

After it finishes, activate the sandbox:

- **Windows:** `sandbox\.venv\Scripts\activate`
- **macOS/Linux:** `source sandbox/.venv/bin/activate`

Then open `sandbox/.env` and fill in your secrets.

## Build the standalone Windows `.exe`

The tool uses only the Python standard library, so it bundles cleanly with
[PyInstaller](https://pyinstaller.org/). **Run this on Windows** (PyInstaller
does not cross-compile):

```bat
tools\sandbox-setup\build_exe.bat
```

or manually:

```bash
pip install pyinstaller
python tools/sandbox-setup/build_exe.py
```

The executable is written to `tools/sandbox-setup/dist/sandbox-setup.exe`. You
can copy it anywhere and double-click or run it from a terminal:

```bat
sandbox-setup.exe C:\my-course-folder
```

> **Note:** When run as an `.exe` outside the repo, it can't auto-detect
> `requirements.txt`/`.env.example`. Pass `--requirements path\to\requirements.txt`
> to install dependencies, or use `--no-install`; the `.env` template falls back
> to a built-in copy of the course keys.
