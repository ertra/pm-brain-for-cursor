# PM Brain setup

The user invoked **`/setup`** to prepare the Python environment for this repo.

## Python virtual environment

This repo expects a local virtualenv at `.venv/` (ignored by git).

- **If `.venv/` is missing:** create it from the project root, then upgrade pip and install dependencies (needs network for pip):

  ```bash
  python3 -m venv .venv
  .venv/bin/python3 -m pip install --upgrade pip
  .venv/bin/pip install -r requirements.txt
  ```

  On Windows, use `.venv\Scripts\python` instead of `.venv/bin/python3`, and `.venv\Scripts\pip` instead of `.venv/bin/pip`.

- **If `.venv/` already exists:** optionally run `.venv/bin/python3 -m pip install --upgrade pip`, then `.venv/bin/pip install -r requirements.txt` so pip and dependencies match current `requirements.txt` (user may skip if they prefer not to upgrade).

- **Activate for this session** when you open a shell in the repo: `source .venv/bin/activate` (Windows: `.venv\Scripts\activate`).

- **On project open:** [`.vscode/settings.json`](../../.vscode/settings.json) sets `python.defaultInterpreterPath` to `.venv` and `python.terminal.activateEnvironment` so new integrated terminals auto-activate that env when the Python extension is active.

If `python3` or venv creation fails, tell the user what broke and what to install (e.g. Python 3 from [python.org](https://www.python.org/) or their OS package manager).

**Done:** confirm `.venv` exists, pip was upgraded (or note if skipped), dependencies are installed (or note what was skipped), and the env is active for any follow-up commands you run.
