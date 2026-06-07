# AGENTS.md — project rules for AI coding assistants

> This file is read by AI coding agents (Claude Code, Cursor, OpenCode,
> GitHub Copilot Workspace, etc.) before they touch this project. If
> you're a human reading this, the short version: **the rules below
> exist because a previous AI agent took a shortcut and broke the
> environment. Don't be that agent.**

## The golden rules

### 1. ALWAYS use `uv`, NEVER bare `python` or `pip install`

```bash
# ✅ Correct
uv run python scripts/doctor.py
uv run streamlit run app.py
uv pip install some-package   # only if you also update pyproject.toml

# ❌ Banned
python scripts/doctor.py
pip install some-package
python -m pip install some-package
```

**Why:** Bare `python` resolves to the system interpreter (or a wrong one
on Windows with multiple Python installs). `pip install` without
`uv` puts packages in the wrong place. This project uses a project-local
`.venv/` that `uv` manages. If you skip `uv`, you'll either:
- Pollute the system Python (Windows: `%APPDATA%\Python\Python3XX\site-packages`)
- Get `ModuleNotFoundError` because your shell's `python` isn't the venv's
- Break the project for the next person

### 2. ALWAYS activate the venv before any code change

```bash
# One-time per shell session
uv sync                     # creates .venv/ if missing, syncs deps
source .venv/bin/activate   # Linux/macOS
# or on Windows:
.venv\Scripts\activate

# Verify
which python    # must show .venv/bin/python or .venv\Scripts\python.exe
```

### 3. To add a dependency: edit `pyproject.toml`, never just `uv pip install`

```bash
# ✅ Correct
# 1. edit pyproject.toml: add "new-package>=1.0" under [project] dependencies
# 2. uv lock
# 3. uv sync
# 4. commit pyproject.toml + uv.lock

# ❌ Banned — leaves pyproject.toml out of sync
uv pip install new-package
```

### 4. NEVER touch the system Python

- No `pip install --user` (Windows puts it in `%APPDATA%\Python\`)
- No `pip install` outside a venv
- No `winget install Python.Python.X.Y` (creates another system Python that conflicts)

If you see a `ModuleNotFoundError`, the fix is NEVER to install
globally. The fix is to make sure you're inside `uv run`.

### 5. Set `PYTHONIOENCODING=utf-8` for any subprocess or script

This project deals with Chinese prompts and emoji output. Windows
defaults to GBK and will crash on the first `🔍` character.

```python
# In any Python script that runs subprocesses
import os, subprocess
env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
subprocess.run(..., env=env)
```

```bash
# In any shell that runs Python
set PYTHONIOENCODING=utf-8    # cmd
$env:PYTHONIOENCODING = "utf-8"  # PowerShell
```

## Project conventions

### Project layout

```
ai-asset-forge/
├── app.py                  # Streamlit UI entry — only file that imports streamlit at top level
├── i18n.py                 # en/zh translation dict + t() helper
├── start.bat               # Windows launcher
├── pyproject.toml          # Dependency manifest (replaces requirements.txt)
├── uv.lock                 # Locked versions (commit this!)
├── .venv/                  # Local venv (gitignored)
├── .streamlit/config.toml  # Streamlit server config (binds 127.0.0.1)
├── config/minimax.json.example  # Template — copy to minimax.json to use
├── prompts/                # M3 system prompts
├── scripts/                # CLI scripts (doctor / plan / generate / index)
├── templates/              # Example plan.json
├── docs/screenshots/       # README images
└── tests/                  # (future) pytest
```

### How to run things

```bash
# Diagnose API connectivity
uv run python scripts/doctor.py

# Generate a plan from a design doc
uv run python scripts/plan.py path/to/design.md

# Generate assets for a project
uv run python scripts/generate.py "项目名" --skip video

# Rebuild the library index
uv run python scripts/index.py --rebuild

# Launch the UI
uv run streamlit run app.py
```

### How to add a new dependency

1. Add the package to `[project].dependencies` in `pyproject.toml`
2. Run `uv lock` to update `uv.lock`
3. Run `uv sync` to install it in the venv
4. Commit BOTH `pyproject.toml` and `uv.lock` (never one without the other)

### How to add a new dev tool (playwright, pytest, etc.)

1. Add to `[dependency-groups].dev` in `pyproject.toml`
2. `uv lock && uv sync`
3. `uv run --group dev pytest` (or whatever) — note: dev groups are
   installed by default, but you can opt out with `uv sync --no-group dev`

### How to take a new screenshot for the README

```bash
# One-time: install playwright browser (huge download, ~200MB)
uv run playwright install chromium

# Run the screenshot script
uv run python scripts/screenshot.py
# (if scripts/screenshot.py doesn't exist yet, write one using playwright sync API)
```

### Committing

- **Never** commit `.venv/`, `__pycache__/`, `*.pyc`, `.env`, real `config/minimax.json`
- **Always** commit `pyproject.toml` and `uv.lock` together
- The CI on GitHub Actions (when added) will run `uv sync` and
  `uv run python -m py_compile` to catch lockfile drift
- If a test fails on CI but passes locally, the first thing to check
  is whether you committed both files

### README and docs

- README is **bilingual** (`README.md` is English default, `README.zh.md` is Chinese)
- If you change one, **update the other in the same commit**
- If you add a new i18n key in `i18n.py`, add it to **both** `en` and `zh` dicts
- Missing translations fall back to the key string itself — easy to spot in the UI

### The M3 planning prompt

- Default: `prompts/resource-planner.md` (Chinese)
- English alternative: `prompts/resource-planner.en.md`
- Edit `scripts/plan.py` `PROMPT_PATH` to switch which one loads
- DO NOT change the JSON schema in the prompt — `scripts/plan.py` parses it

### API keys and secrets

- `config/minimax.json` is **gitignored** and contains real keys
- The committed template is `config/minimax.json.example`
- If you accidentally see a real key in a file, **do not commit it**
- The project uses two keys: `api_key` (Token Plan) and optionally
  `payg_api_key` (PAYG for M3 text). The latter falls back to `api_key` if empty

## Pre-flight checklist before committing

```bash
# 1. Does it still import?
uv run python -c "import app, i18n; from scripts import doctor, plan, generate, index"

# 2. Does doctor.py still work? (skip if you don't have API keys)
# uv run python scripts/doctor.py

# 3. Did you add a new i18n key to both en and zh?
grep -c "your_new_key" i18n.py   # should be 2 (en + zh)

# 4. Did you commit pyproject.toml AND uv.lock together?
git status pyproject.toml uv.lock
# both should be modified, or both unchanged
```

## When in doubt

- Read the existing code first. This project has 4 CLI scripts and 1
  UI; they're all short (< 500 lines each). Read them before changing them.
- Don't refactor. The CLAUDE.md rule "surgical changes" applies here too.
  The user is the only maintainer right now. They want changes they
  understand.
- When something is unclear, ask the user. Don't guess — they'll
  appreciate the question more than a wrong solution.

## Common mistakes by AI agents (please don't repeat)

| Mistake | Consequence | Fix |
|---|---|---|
| `pip install requests` | pollutes system, project still missing it | delete `%APPDATA%\Python\`, use `uv add` |
| `python scripts/doctor.py` (bare) | runs system Python, can't find deps | use `uv run python scripts/doctor.py` |
| Edit `pyproject.toml` then forget `uv lock` | `uv sync` will fail or produce wrong lock | always `uv lock && uv sync` after editing |
| Edit `uv.lock` by hand | breaks reproducibility | always regenerate via `uv lock` |
| Forget to update `README.zh.md` when changing `README.md` | docs drift | update both in the same commit |
| Add i18n key to `en` but forget `zh` | UI shows the key string | add to both dicts |
| Commit `config/minimax.json` with real key | key leaks to public GitHub | the file is gitignored; double-check before `git add` |
| Use `winget install Python.Python.3.12` | creates system Python that shadows uv's | use `uv python install` |
| `cd some_subdir && uv run ...` | uv can't find pyproject.toml | always run uv from project root |
| Run `python -c "import streamlit"` to test | tests the wrong Python | use `uv run python -c "import streamlit"` |

## TL;DR for a fresh agent

```bash
cd /path/to/ai-asset-forge
uv sync                                    # 2-3 min first time, <1s after
uv run python scripts/doctor.py             # test setup
# make your changes
uv run python -c "import app, i18n; from scripts import doctor, plan, generate, index"
# add deps: edit pyproject.toml, then uv lock && uv sync
# commit
```

That's it. Welcome to the project. Be careful with Python.
