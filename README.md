# 🎮 M3 AIGC Game Asset Pipeline

> One-line pitch: a Streamlit UI that turns a game design document into a generated, indexed, and reusable library of game assets — using [M3](https://api.minimaxi.com) (text / image / video / TTS / music) and the [Token Plan](https://api.minimaxi.com) API.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org)
[![Streamlit](https://img.shields.io/badge/streamlit-1.58-red.svg)](https://streamlit.io)
![Status: Beta](https://img.shields.io/badge/status-beta-orange)

[中文文档](README.zh.md) · [Quick Start](#-quick-start) · [Screenshots](#-screenshots) · [Architecture](#-architecture)

---

## ✨ Features

- **Plan from a design doc** — drop a `.md`/`.txt` of your game idea, M3 turns it into a structured resource plan (characters, scenes, skills, UI, items, BGM, SFX…).
- **Generate all modalities** — image, video, TTS voice lines, instrumental music, and text in one batch. Concurrency, retries, timeouts handled.
- **Smart SFX trimming** — uses ffmpeg's `silencedetect` to find natural endings and `afade` for smooth tails, no abrupt cuts. (Relies on `imageio-ffmpeg`.)
- **Global library index** — SHA-256 deduplication, search by Chinese name / English filename / description / ID, thumbnail + inline audio/video preview.
- **Cross-project reuse** — copy any resource into another project with one click.
- **i18n** — English (default) and 中文 UI, switchable from the sidebar.
- **CLI + GUI** — every UI page wraps a CLI script, so you can script it from cron / CI.

---

## 📸 Screenshots

### Home
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

---

## 🚀 Quick Start

### 1. Install

Requires **Python 3.10+**.

```bash
git clone <your-fork-url>
cd game-asset-pipeline
pip install -r requirements.txt
```

### 2. Configure API keys

Copy the template and fill in your keys:

```bash
cp config/minimax.json.example config/minimax.json
# edit config/minimax.json
```

You need **one or both** of these from [MiniMax platform](https://api.minimaxi.com):

| Key | Used by | Where to get it |
|---|---|---|
| `api_key` (Token Plan) | image / video / TTS / music (spends credits) | Subscription / Token Plan page |
| `payg_api_key` (PAYG) | M3 text planning (spends tokens) | Pay-as-you-go page |

If you only have a Token Plan key, leave `payg_api_key` empty — M3 text calls will fallback to the Token Plan key.

### 3. Run the UI

```bash
streamlit run app.py
```

Opens `http://localhost:8501` in your browser. (Bound to `127.0.0.1` by default — see [`.streamlit/config.toml`](.streamlit/config.toml).)

Or use the bundled `start.bat` on Windows.

### 4. First project, end-to-end

1. **Doctor** page → click "Run doctor.py" to verify all 5 APIs are reachable.
2. **Plan** page → click "Use project-root design.md" (or upload your own) → click "Run plan.py". Takes 4-8 minutes for M3 to plan.
3. **Generate** page → select the project → check modalities to skip (e.g. `video` if your quota is low) → click "Run generate.py". Takes 5-10 minutes for the first run.
4. **Library** page → search, filter, preview, reuse.

### 5. Just use the CLI

If you don't want the UI, the same scripts work standalone:

```bash
# Diagnose
python scripts/doctor.py

# Plan
python scripts/plan.py path/to/design.md

# Generate
python scripts/generate.py 你的项目名 --skip video

# Rebuild index and search
python scripts/index.py --rebuild
python scripts/index.py --search "李墨寒"
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  design.md  ─►  M3  ─►  plan.json  ─►  APIs  ─►  assets/   │
│                                       │                    │
│                                       ▼                    │
│                                  index.json  ◄── scan       │
│                                       │                    │
│                                       ▼                    │
│                              Streamlit UI (this app)       │
└─────────────────────────────────────────────────────────────┘
```

| Script | Job |
|---|---|
| `scripts/doctor.py` | One-shot health check for M3 / image / video / TTS / music |
| `scripts/plan.py` | Send design doc to M3, get back structured `plan.json` |
| `scripts/generate.py` | Read `plan.json`, batch-call APIs, download + rename + save |
| `scripts/index.py` | Scan all projects, build searchable `index.json` |
| `app.py` | Streamlit UI wrapping the above 4 scripts |
| `i18n.py` | en/zh translation dictionary + `t()` helper |

See the [project structure](#-project-structure) for the full layout.

---

## 🗂️ Project structure

```
game-asset-pipeline/
├── app.py                       # Streamlit UI entry
├── i18n.py                      # en / zh translations
├── start.bat                    # Windows launcher (headless-safe)
├── requirements.txt
├── LICENSE                      # MIT
├── README.md / README.zh.md     # this file
├── .streamlit/
│   └── config.toml              # bound to 127.0.0.1:8501
├── config/
│   ├── minimax.json.example     # template (committed)
│   └── minimax.json             # YOUR keys (gitignored)
├── prompts/
│   ├── resource-planner.md      # M3 system prompt
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

`config/minimax.json` fields:

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

The CLI scripts (`scripts/*.py`) print in Chinese by default. If you want them in English, edit them directly — they're short and self-contained.

---

## 🧰 Troubleshooting

**`doctor.py` reports `1004 login fail` on every test** → Your `api_key` is wrong or empty. Edit `config/minimax.json`.

**`doctor.py` reports `usage limit exceeded, daily usage limit reached for Token Plan Max (3/3 used)`** → Video generation is the most expensive; the daily quota is small on lower plans. Run with `--skip video` and retry the next day, or upgrade your plan.

**`plan.py` times out at 5 minutes** → M3 text generation can be slow for very long design docs. Try a shorter doc, or increase the timeout in `scripts/plan.py` (search for `timeout=300`).

**`generate.py` says `invalid params, lyrics is required`** → Shouldn't happen anymore; we always send `is_instrumental: true`. If it does, open an issue.

**Streamlit shows `ModuleNotFoundError: No module named 'streamlit'`** → `pip install -r requirements.txt`.

**Audio in the Library doesn't play** → Check the browser console. The file is read as bytes and embedded — the MIME type is detected from magic numbers, so a corrupted file should show "Audio playback failed: …".

**`imageio-ffmpeg` warnings on first run** → Normal. It downloads a static ffmpeg binary on first use. Subsequent runs are silent.

---

## 🤝 Contributing

PRs welcome. A few things to know:

- **Don't commit your `config/minimax.json`** — it has real API keys. The `.gitignore` already excludes it.
- **Add new i18n keys to BOTH `en` and `zh` in `i18n.py`**.
- **The CLI scripts are the source of truth**. The Streamlit UI is a thin wrapper. Test changes via the CLI first.
- **Run `python scripts/doctor.py`** before opening a PR to make sure your local setup works.

---

## 📜 License

MIT — see [LICENSE](LICENSE).
