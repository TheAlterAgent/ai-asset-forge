# 🔥 AI Asset Forge

> **Your AI-generated game assets don't have to be one-shot. They evolve, branch, and grow — like a family tree.**
>
> AI Asset Forge is a generator + library + version graph for game assets, built for solo devs and artists who want AI assistance without losing creative control. Currently powered by MiniMax / M3, designed to support more model backends.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org)
[![Streamlit](https://img.shields.io/badge/streamlit-1.58-red.svg)](https://streamlit.io)
![Status: Beta](https://img.shields.io/badge/status-beta-orange)

[中文文档](README.zh.md) · [Quick Start](#-quick-start) · [Roadmap](#-roadmap) · [The core idea](#-the-core-idea-assets-have-a-family-tree)

---

## 🎯 Who is this for?

**You don't have an art team. You do have ideas.**

Two kinds of users:

1. **The programmer with no artist** — you can write the logic, you can't draw the sprites. You want a generator that turns design docs into assets, and a manager that keeps them organized across projects.
2. **The artist who wants AI assistance** — you have the original skill, but you want to use AI to multiply yourself. You create one piece, then let AI generate variations; you pick what works, refine, branch. Over time your personal style evolves through a tree of derivatives.

Both users end up with the same problem: **too many assets, no way to see which came from which, no way to manage the iterative mess**. AI Asset Forge is for both.

---

## ✨ Features

### Today (shipped)
- **Generate from a design doc** — feed in a `.md`/`.txt`, M3 turns it into a structured resource plan (characters, scenes, skills, UI, items, BGM, SFX).
- **All modalities** — image, video, TTS voice, instrumental music, and text, batched with retries and timeouts.
- **Smart SFX trimming** — ffmpeg's `silencedetect` + `afade` for natural endings, no abrupt 5 MB clicks.
- **Global library index** — SHA-256 dedup, search by Chinese name / English filename / description / ID, inline audio/video preview.
- **Cross-project reuse** — copy any resource into another project with one click.
- **i18n** — English (default) and 中文 UI.
- **CLI + GUI** — every UI page wraps a CLI script, scriptable from CI/cron.

### The core idea (see [Roadmap](#-roadmap) for status)
- **Every asset has a family tree** — each asset knows its parent (the source image / prompt that produced it) and its children (the variants it spawned). The whole library is a navigable graph.
- **Visual tree view** — pan/zoom, left/right or up/down, like a 族谱 (family tree). Click any node to see its ancestry, descendants, the exact prompt that produced it, and the original seed image.
- **Fork, refine, share** — anyone in your team can branch off a popular asset, run it through AI again, upload the result back as a child node. The best variants accumulate.
- **Mix AI + manual** — drop in your own PNG/JPG/MP3. It becomes a first-class node in the same graph, indistinguishable from AI-generated ones. No "AI vs hand-made" split.

---

## 🌱 The core idea: assets have a family tree

AI generation is rarely one-shot. A good asset is **iterated on** — an original concept, refined with AI, refined again, branched into variants, picked, refined again.

AI Asset Forge treats every asset as a node in an **evolution graph**:

```
                        ┌─────────────┐
                        │ original    │  ← you painted it, or generated the first version
                        │ hero_idle   │
                        └──────┬──────┘
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
       ┌──────────┐       ┌──────────┐       ┌──────────┐
       │ battle-1 │       │ portrait │       │ idle-v2  │
       │ damage   │       │ close-up │       │ new pose │
       └────┬─────┘       └────┬─────┘       └──────────┘
            │                  │
       ┌────┴─────┐       ┌────┴─────┐
       ▼          ▼       ▼          ▼
   ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
   │ on-fire│ │ rainy  │ │ wounded│ │ smiling│
   └────────┘ └────────┘ └────────┘ └────────┘
     (fork)      (fork)     (fork)      (fork)
```

Every node carries:
- The **asset file** (PNG, MP3, etc.)
- The **prompt** that produced it (or, for hand-imported, the user's notes)
- The **parent reference** (the asset it was derived from, if any)
- **Generation metadata** (model, seed, settings, timestamp)
- **Tags** for searchability

You can:
- Click any node to see its full ancestry (the chain of prompts/seed images that produced it).
- See who in your team forked your work and how.
- Branch off in multiple directions and pick the winner later.
- Roll back to any previous version, like git history for art.

The tree view will be pan/zoom, left/right or up/down, inspired by GitKraken's commit graph and traditional 族谱 charts.

---

## 📸 Screenshots

### Home — see all your projects at a glance
![Dashboard](docs/screenshots/01-dashboard.png)

### Library — search, filter, preview, reuse
![Library](docs/screenshots/02-library.png)

### Generate — pick a project, configure, run
![Generate](docs/screenshots/03-generate.png)

### Plan — upload a design doc, let M3 plan it
![Plan](docs/screenshots/04-plan.png)

### Doctor — one-click API health check
![Doctor](docs/screenshots/05-doctor.png)

### 中文界面
![Chinese UI](docs/screenshots/06-zh-dashboard.png)

> **Coming soon** (mockup): pan/zoom **family tree** view of asset evolution.

---

## 🚀 Quick Start

### 1. Install

Requires **[uv](https://docs.astral.sh/uv/)** (the modern Python package manager). Install it via `winget` on Windows, or `brew install uv` / `curl install` on macOS/Linux — see [uv install docs](https://docs.astral.sh/uv/getting-started/installation/).

```bash
git clone https://github.com/TheAlterAgent/ai-asset-forge.git
cd ai-asset-forge
uv sync                # creates .venv/ and installs everything from uv.lock
```

> **Why `uv` and not `pip install -r requirements.txt`?**
> - This project uses `pyproject.toml` + `uv.lock` (not a hand-rolled `requirements.txt`).
> - `uv` is 10-100x faster than pip, manages Python versions, and refuses to pollute your system Python.
> - **AI agents / contributors: see [AGENTS.md](AGENTS.md) — the rules are non-negotiable.**

### 2. Configure a backend

```bash
cp config/minimax.json.example config/minimax.json
# edit config/minimax.json
```

See [Backends](#-backends) for what to put here. Today there's one working backend: **MiniMax**. You'll need one or both of:

| Key | Used by | Where to get it |
|---|---|---|
| `api_key` (Token Plan) | image / video / TTS / music (spends credits) | [MiniMax Token Plan page](https://api.minimaxi.com) |
| `payg_api_key` (PAYG) | M3 text planning (spends tokens) | MiniMax PAYG page |

If you only have a Token Plan key, leave `payg_api_key` empty — M3 text calls will fall back to the Token Plan key.

### 3. Run the UI

```bash
uv run streamlit run app.py
```

Opens `http://localhost:8501` in your browser. (Bound to `127.0.0.1` by default — see [`.streamlit/config.toml`](.streamlit/config.toml).)

On Windows you can also double-click `start.bat` (which uses the system Python — see [AGENTS.md](AGENTS.md) for the recommended `uv` flow).

### 4. Your first project, end-to-end

1. **Doctor** page → click "Run doctor.py" to verify all 5 APIs are reachable.
2. **Plan** page → click "Use project-root design.md" (or upload your own) → click "Run plan.py". Takes 4-8 minutes for M3 to plan.
3. **Generate** page → select the project → check modalities to skip (e.g. `video` if your quota is low) → click "Run generate.py". Takes 5-10 minutes for the first run.
4. **Library** page → search, filter, preview, reuse. Make another project and reuse assets from this one.

### 5. Just use the CLI

Don't want the UI? The same scripts work standalone — always with `uv run`:

```bash
uv run python scripts/doctor.py
uv run python scripts/plan.py path/to/design.md
uv run python scripts/generate.py 你的项目名 --skip video
uv run python scripts/index.py --rebuild
uv run python scripts/index.py --search "李墨寒"
```

---

## 🔌 Backends

The generator is designed around **pluggable backends** so it can grow beyond a single model provider.

| Backend | Status | What you get |
|---|---|---|
| **MiniMax** (M3 + Token Plan) | ✅ Working | Text planning (M3), image (`image-01`), video (`Hailuo-2.3`), TTS (`speech-2.6-hd`), music (`music-2.6`) |
| **Stable Diffusion** (local) | 🔜 Planned | Image, img2img variations — privacy-friendly, free, offline |
| **DALL-E / GPT-4o** | 🔜 Planned | Image generation |
| **ComfyUI workflows** | 🔜 Planned | Custom pipelines you define |
| **Local checkpoints** (SD / Flux / etc.) | 🔜 Planned | Any local model you can run |

Want to add one? See [Contributing](#-contributing) — the backend interface is designed to be small.

---

## 🗂 Roadmap

The **vision** is the family tree above. The current shipped scope is the foundation. Here's the order we're likely to build in:

| Priority | Feature | Why |
|---|---|---|
| ✅ done | Multi-backend generation (MiniMax) | Foundation — assets must exist before they can have a tree |
| ✅ done | Library index + search + reuse | Foundation — need a way to find assets |
| ✅ done | Smart SFX trimming | Polish — better SFX = more useful tree |
| 🔜 next | **Asset lineage graph** | The core idea — every asset gets a `parent_id`; CLI can show ancestry |
| 🔜 next | **Manual asset import** | Drop in your own PNG/JPG/MP3, it becomes a first-class node |
| 🔜 next | **Tree visualization** | Pan/zoom graph view in the UI |
| ⏳ later | **Pluggable backends** | SD/DALL-E/ComfyUI/etc. |
| ⏳ later | **Derivative generation from owned assets** | "Same character but on fire" using your existing asset as seed |
| ⏳ later | **Asset version control** | Every save is a revision, roll back, diff, branch tags |
| ⏳ later | **Team sharing** | Fork someone else's asset, contribute back |
| 💭 idea | **Style transfer from your library** | Use your own finished assets to teach the AI your style |

> Want to influence priority? Open an issue, or just use the tool and tell us what's missing.

---

## 🔧 How it works

```
┌─────────────────────────────────────────────────────────────┐
│                                                              │
│  design.md / prompt ─► AI backend ─► new asset (child of X)  │
│                                           │                  │
│                                           ▼                  │
│              assets/  ◄──  version store  +  lineage DAG     │
│                       │                                      │
│                       ▼                                      │
│                index.json + parent_id links                  │
│                       │                                      │
│                       ▼                                      │
│             Streamlit UI  +  tree view  (planned)            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

| Script | Job |
|---|---|
| `scripts/doctor.py` | One-shot health check for all backends |
| `scripts/plan.py` | Send design doc to the text backend, get back structured `plan.json` |
| `scripts/generate.py` | Read `plan.json`, batch-call APIs, download + save (with `parent_id` for lineage) |
| `scripts/index.py` | Scan all projects, build searchable `index.json` |
| `app.py` | Streamlit UI wrapping the above 4 scripts |
| `i18n.py` | en/zh translation dictionary + `t()` helper |

See [Project structure](#-project-structure) for the full layout.

---

## 🗂️ Project structure

```
game-asset-pipeline/             ← local directory name (the GitHub repo can be renamed)
├── app.py                       # Streamlit UI entry
├── i18n.py                      # en / zh translations
├── AGENTS.md                    # rules for AI coding agents (read this first!)
├── start.bat                    # Windows launcher (headless-safe)
├── pyproject.toml               # dependency manifest
├── uv.lock                      # locked versions (commit this!)
├── .venv/                       # local venv (gitignored) — created by `uv sync`
├── LICENSE                      # MIT
├── README.md / README.zh.md     # this file
├── .streamlit/
│   └── config.toml              # bound to 127.0.0.1:8501
├── config/
│   ├── minimax.json.example     # template (committed)
│   └── minimax.json             # YOUR keys (gitignored)
├── prompts/
│   ├── resource-planner.md      # M3 system prompt (Chinese, default)
│   ├── resource-planner.en.md   # M3 system prompt (English)
│   └── modality-prompts/        # future: per-modality prompts
├── scripts/
│   ├── doctor.py
│   ├── plan.py
│   ├── generate.py
│   └── index.py
├── templates/
│   └── project-template.json    # example plan.json for testing
└── docs/
    └── screenshots/             # README images
```

`assets/projects/<项目名>/` is gitignored — it's your own generated content, not source.

---

## ⚙️ Configuration reference

`config/minimax.json` fields (will become backend-specific in future versions):

| Field | Required | Notes |
|---|---|---|
| `api_base` | ✓ | Usually `https://api.minimaxi.com` |
| `api_key` | ✓ | Token Plan key — image / video / TTS / music |
| `payg_api_key` | optional | PAYG key for M3 text (falls back to `api_key` if empty) |
| `group_id` | optional | Only needed for some endpoints |
| `models.text` | ✓ | Default `MiniMax-M3` |
| `models.image` | ✓ | Default `image-01` |
| `models.video` | ✓ | Default `MiniMax-Hailuo-2.3` (daily quota: 3 on Max plan) |
| `models.tts` | ✓ | Default `speech-2.6-hd` |
| `models.music` | ✓ | Default `music-2.6` |
| `output_dir` | ✓ | Where projects live (relative to repo root) |
| `max_concurrent` | ✓ | Parallel API calls (video ≤ 2, others can be higher) |
| `retry_times` | ✓ | Retry attempts on transient failures |

---

## 🌍 Internationalization

The UI supports **English** (default) and **中文**. Switch via the language picker in the sidebar.

To add a new language:
1. Open `i18n.py`
2. Add a new entry to `LANGS` with the same keys as `"en"` and translated values
3. Add a label in `language_picker()` in `i18n.py`

Missing translation keys fall back to the key itself, so they're easy to spot in the UI.

The M3 planning prompt is also available in both languages: `prompts/resource-planner.md` (Chinese, default) and `prompts/resource-planner.en.md` (English). Switch by renaming or by editing `scripts/plan.py` to point to the other file.

The CLI scripts (`scripts/*.py`) print in Chinese by default. If you want them in English, edit them directly — they're short and self-contained.

---

## 🧰 Troubleshooting

**`doctor.py` reports `1004 login fail` on every test** → Your `api_key` is wrong or empty. Edit `config/minimax.json`.

**`doctor.py` reports `usage limit exceeded, daily usage limit reached for Token Plan Max (3/3 used)`** → Video generation is the most expensive; the daily quota is small on lower plans. Run with `--skip video` and retry the next day, or upgrade your plan.

**`plan.py` times out at 5 minutes** → M3 text generation can be slow for very long design docs. Try a shorter doc, or increase the timeout in `scripts/plan.py` (search for `timeout=300`).

**`generate.py` says `invalid params, lyrics is required`** → Shouldn't happen anymore; we always send `is_instrumental: true`. If it does, open an issue.

**Streamlit shows `ModuleNotFoundError: No module named 'streamlit'`** → `uv sync` (not `pip install`).

**Audio in the Library doesn't play** → Check the browser console. The file is read as bytes and embedded — the MIME type is detected from magic numbers, so a corrupted file should show "Audio playback failed: …".

**`imageio-ffmpeg` warnings on first run** → Normal. It downloads a static ffmpeg binary on first use. Subsequent runs are silent.

---

## 🤝 Contributing

PRs welcome. Especially welcome:
- **New backends** — the backend interface is small, designed to be plugged into.
- **Tree visualization** — d3 / vis.js / react-flow / your favorite.
- **i18n translations** — anything beyond en/zh.
- **Tests** for the existing scripts.

Things to know:
- **Don't commit your `config/minimax.json`** — it has real API keys. The `.gitignore` already excludes it.
- **Add new i18n keys to BOTH `en` and `zh` in `i18n.py`**.
- **The CLI scripts are the source of truth**. The Streamlit UI is a thin wrapper. Test changes via the CLI first.
- **Run `python scripts/doctor.py`** before opening a PR to make sure your local setup works.

---

## 📜 License

MIT — see [LICENSE](LICENSE).
