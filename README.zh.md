# 🔥 AI Asset Forge

> **从一份游戏设计文档，到一个可玩 demo——不需要美术。**
>
> AI Asset Forge 用 [M3](https://api.minimaxi.com)（文本/图像/视频/TTS/音乐）把你的游戏想法变成可生成、可索引、可复用的资产生成与管理工具。为没有美术团队的单人开发者、爱好者、学生设计。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org)
[![Streamlit](https://img.shields.io/badge/streamlit-1.58-red.svg)](https://streamlit.io)
![状态: Beta](https://img.shields.io/badge/status-beta-orange)

[English README](README.md) · [快速开始](#-快速开始) · [截图](#-截图) · [怎么工作的](#-怎么工作的)

---

## 🎯 这是给谁用的？

你是个程序员，或者爱好者、学生、小团队。你脑子里有游戏点子，逻辑能写出来。**但你不会画画，也请不起美术团队。** 你想做个 demo 去路演、测试、或者自己玩玩。

AI Asset Forge 就是给你用的。丢一份设计文档进去，出来一整套资源库：角色（带语音）、场景（带环境音）、技能图标、UI、BGM、SFX。可搜索、去重、跨项目复用。

## ✨ 特性

- **从设计文档生成规划** — 拖一个 `.md`/`.txt` 进去，M3 拆解成结构化资源清单（角色/场景/技能/UI/道具/BGM/SFX…）
- **全模态批量生成** — 图像、视频、TTS 语音、器乐、文字一锅端，并发、重试、超时都处理好
- **SFX 智能裁剪** — 用 ffmpeg 的 `silencedetect` 找自然结束点 + `afade` 加淡出，不硬切（依赖 `imageio-ffmpeg`）
- **全局资源索引** — SHA256 去重，按中文名/英文文件名/描述/ID 搜索，缩略图 + 内嵌音频/视频预览
- **跨项目复用** — 一键把任意资源复制到别的项目。建一次个人素材库，到处用
- **i18n** — 英文（默认）和中文，sidebar 一键切换
- **CLI + GUI 都有** — 每个 UI 页面背后就是一个 CLI 脚本，可以塞 cron / CI / 自己的流水线

## 📸 截图

### 概览 — 一眼看所有项目
![Dashboard](docs/screenshots/01-dashboard.png)

### 资源库 — 搜索、筛选、预览、复用
![Library](docs/screenshots/02-library.png)

### 生成 — 选项目、配参数、跑
![Generate](docs/screenshots/03-generate.png)

### 规划 — 上传设计文档，让 M3 拆解
![Plan](docs/screenshots/04-plan.png)

### 诊断 — 一键 API 健康检查
![Doctor](docs/screenshots/05-doctor.png)

### 英文界面
![English UI](docs/screenshots/06-zh-dashboard.png)

---

## 🚀 快速开始

### 1. 安装

需要 **Python 3.10+**。

```bash
git clone <your-fork-url>
cd game-asset-pipeline
pip install -r requirements.txt
```

### 2. 配置 API Key

```bash
cp config/minimax.json.example config/minimax.json
# 编辑 config/minimax.json
```

你需要一个或两个 key（从 [MiniMax 开放平台](https://api.minimaxi.com) 控制台拿）：

| Key | 用途 | 哪里拿 |
|---|---|---|
| `api_key`（Token Plan） | 图像/视频/TTS/音乐（扣积分） | 订阅 / Token Plan 页面 |
| `payg_api_key`（PAYG） | M3 文本规划（按 token 计费） | 按量计费页面 |

只买了 Token Plan 的话，`payg_api_key` 留空即可——M3 文本调用会自动 fallback 到 `api_key`。

### 3. 启动 UI

```bash
streamlit run app.py
```

浏览器自动打开 `http://localhost:8501`（默认绑 127.0.0.1，看 [`.streamlit/config.toml`](.streamlit/config.toml)）。Windows 也可以双击 `start.bat`。

### 4. 第一个项目，端到端走一遍

1. **🔍 诊断** 页 → 点 "Run doctor.py"，确认 5 个 API 都能连通
2. **🧠 规划** 页 → 点 "Use project-root design.md"（或上传自己的）→ 点 "Run plan.py"。M3 分析 4-8 分钟
3. **⚙️ 生成** 页 → 选刚生成的项目 → 勾选要跳过的模态（比如 `video` 因为配额少）→ 点 "Run generate.py"。第一次跑 5-10 分钟
4. **📚 资源库** 页 → 搜索、筛选、预览、复用。多开几个项目，资源互通

### 5. 只用 CLI

不要 UI 的话，同一套脚本也能直接跑：

```bash
# 诊断
python scripts/doctor.py

# 规划
python scripts/plan.py path/to/design.md

# 生成
python scripts/generate.py 你的项目名 --skip video

# 建索引 + 搜索
python scripts/index.py --rebuild
python scripts/index.py --search "李墨寒"
```

---

## 🔧 怎么工作的

```
┌─────────────────────────────────────────────────────────────┐
│  design.md  ─►  M3  ─►  plan.json  ─►  API  ─►  assets/    │
│                                       │                    │
│                                       ▼                    │
│                              index.json  ◄── scan          │
│                                       │                    │
│                                       ▼                    │
│                          Streamlit UI (本 app)              │
└─────────────────────────────────────────────────────────────┘
```

| 脚本 | 作用 |
|---|---|
| `scripts/doctor.py` | 一次性检查 M3 / 图像 / 视频 / TTS / 音乐连通性 |
| `scripts/plan.py` | 把设计文档发给 M3，拿到结构化 `plan.json` |
| `scripts/generate.py` | 读 `plan.json`，批量调 API，下载 + 改名 + 入库 |
| `scripts/index.py` | 扫所有项目，建可搜索的 `index.json` |
| `app.py` | 包了上面 4 个脚本的 Streamlit UI |
| `i18n.py` | en / zh 翻译字典 + `t()` helper |

完整结构见 [项目结构](#-项目结构)。

---

## 🗂️ 项目结构

```
game-asset-pipeline/             ← 本地目录名（GitHub 仓库可以重命名）
├── app.py                       # Streamlit UI 入口
├── i18n.py                      # en / zh 翻译
├── start.bat                    # Windows 启动器（防卡邮箱引导）
├── requirements.txt
├── LICENSE                      # MIT
├── README.md / README.zh.md     # 本文件
├── .streamlit/
│   └── config.toml              # 绑 127.0.0.1:8501
├── config/
│   ├── minimax.json.example     # 模板（提交进 git）
│   └── minimax.json             # 你的真 key（gitignore 掉）
├── prompts/
│   ├── resource-planner.md      # M3 系统 prompt（中文，默认）
│   ├── resource-planner.en.md   # M3 系统 prompt（英文）
│   └── modality-prompts/        # 预留：各模态 prompt
├── scripts/
│   ├── doctor.py
│   ├── plan.py
│   ├── generate.py
│   └── index.py
├── templates/
│   └── project-template.json    # 测试用示例 plan
└── docs/
    └── screenshots/             # README 截图
```

`assets/projects/<项目名>/` 在 `.gitignore` 里——这是你自己生成的内容，不该当源码提交。

---

## ⚙️ 配置项参考

`config/minimax.json` 字段：

| 字段 | 必填 | 说明 |
|---|---|---|
| `api_base` | ✓ | 通常 `https://api.minimaxi.com` |
| `api_key` | ✓ | Token Plan Key — 图像/视频/TTS/音乐 |
| `payg_api_key` | 否 | PAYG Key 给 M3 文本用（空则 fallback 到 `api_key`） |
| `group_id` | 否 | 部分端点需要 |
| `models.text` | ✓ | 默认 `MiniMax-M3` |
| `models.image` | ✓ | 默认 `image-01` |
| `models.video` | ✓ | 默认 `MiniMax-Hailuo-2.3`（Max 套餐每天 3 次） |
| `models.tts` | ✓ | 默认 `speech-2.6-hd` |
| `models.music` | ✓ | 默认 `music-2.6` |
| `output_dir` | ✓ | 项目产出位置（相对仓库根） |
| `max_concurrent` | ✓ | 并发 API 调用数（视频 ≤2，其他可调高） |
| `retry_times` | ✓ | 临时失败重试次数 |

---

## 🌍 国际化

UI 支持 **英文**（默认）和 **中文**，sidebar 一键切换。

加新语言：
1. 打开 `i18n.py`
2. 在 `LANGS` 字典里加一项，key 跟 `"en"` 一样，value 翻译
3. 在 `language_picker()` 里加标签

漏翻译的 key 会回退到 key 本身，UI 上能直接看到该补的词。

M3 规划 prompt 也是双语：`prompts/resource-planner.md`（中文，默认）和 `prompts/resource-planner.en.md`（英文）。改文件名切换，或改 `scripts/plan.py` 里的路径。

CLI 脚本（`scripts/*.py`）默认打印中文。要英文直接改源码就行——每个脚本都很短。

---

## 🧰 排错

**`doctor.py` 全报 `1004 login fail`** → `api_key` 错了或留空，编辑 `config/minimax.json`。

**`doctor.py` 报 `usage limit exceeded, daily usage limit reached for Token Plan Max (3/3 used)`** → 视频生成最耗积分，低档套餐每天就 3 次。加 `--skip video` 明天再试，或者升套餐。

**`plan.py` 5 分钟超时** → M3 对超长设计文档很慢。文档精简点，或在 `scripts/plan.py` 里把 `timeout=300` 调大。

**`generate.py` 报 `invalid params, lyrics is required`** → 不该再出现了，我们总是传 `is_instrumental: true`。碰到了开个 issue。

**Streamlit 报 `ModuleNotFoundError: No module named 'streamlit'`** → `pip install -r requirements.txt`。

**资源库里音频播不了** → 打开浏览器控制台看报错。文件是按字节流嵌入的，MIME type 走 magic number 探测，文件坏了会显示 "Audio playback failed: …"。

**`imageio-ffmpeg` 第一次跑有 warning** → 正常，第一次会下载静态 ffmpeg 二进制。后面就没了。

---

## 🤝 贡献

欢迎 PR。几个注意点：

- **别把 `config/minimax.json` 提交** — 里面有真 API key，`.gitignore` 已经排除
- **加新 i18n key 时，`en` 和 `zh` 都要补**（`i18n.py`）
- **CLI 脚本是 source of truth**，Streamlit 只是薄壳。改完先用 CLI 测一遍
- **提 PR 前跑一次 `python scripts/doctor.py`**，确认你本地环境没问题

---

## 📜 License

MIT — 见 [LICENSE](LICENSE)。
