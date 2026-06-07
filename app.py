"""
M3 AIGC Game Asset Pipeline - Streamlit UI

Usage:
    streamlit run app.py

Opens http://localhost:8501 in your browser.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import streamlit as st

from i18n import t, language_picker

BASE_DIR = Path(__file__).parent
SCRIPTS_DIR = BASE_DIR / "scripts"
ASSETS_DIR = BASE_DIR / "assets"
PROJECTS_DIR = ASSETS_DIR / "projects"
INDEX_PATH = ASSETS_DIR / "index.json"
CONFIG_PATH = BASE_DIR / "config" / "minimax.json"

ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}

st.set_page_config(
    page_title="M3 Game Asset Pipeline",
    page_icon="🎮",
    layout="wide",
)


# ---------- Helpers ----------

def list_projects() -> list[dict]:
    out = []
    if not PROJECTS_DIR.exists():
        return out
    for d in sorted(PROJECTS_DIR.iterdir()):
        if not d.is_dir() or not (d / "plan.json").exists():
            continue
        try:
            with open(d / "plan.json", encoding="utf-8") as f:
                plan = json.load(f)
        except Exception:
            plan = {}
        report = None
        if (d / "report.json").exists():
            try:
                with open(d / "report.json", encoding="utf-8") as f:
                    report = json.load(f)
            except Exception:
                report = None
        out.append({
            "name": d.name,
            "dir": d,
            "plan": plan,
            "report": report,
        })
    return out


@st.cache_data(ttl=5)
def load_index() -> dict | None:
    if not INDEX_PATH.exists():
        return None
    with open(INDEX_PATH, encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(ttl=5)
def load_plan(project_name: str) -> dict | None:
    p = PROJECTS_DIR / project_name / "plan.json"
    if not p.exists():
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def run_subprocess(cmd: list[str], cwd: Path | None = None) -> tuple[int, str]:
    """Run subprocess, streaming output into an st.empty() area. Returns (returncode, full_output)."""
    output_area = st.empty()
    output = ""
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(cwd) if cwd else None,
            env=ENV,
        )
        for line in proc.stdout:
            output += line
            output_area.code(output)
        proc.wait()
        return proc.returncode, output
    except FileNotFoundError as e:
        return -1, f"Executable not found: {e}"
    except Exception as e:
        return -1, f"Launch failed: {e}"


def run_script(script: str, args: list[str], cwd: Path | None = None) -> tuple[int, str]:
    cmd = [sys.executable, str(SCRIPTS_DIR / script), *args]
    return run_subprocess(cmd, cwd=cwd or BASE_DIR)


def safe_name(s: str) -> str:
    return "".join(c if c.isalnum() or c in "_-" else "_" for c in s)


def detect_audio_mime(data: bytes) -> str:
    """Detect real audio format from file header magic (not extension — TTS returns MP3 saved as .wav)."""
    if not data:
        return "audio/mpeg"
    if data[:3] == b"ID3" or (data[0] == 0xFF and (data[1] & 0xE0) == 0xE0):
        return "audio/mpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WAVE":
        return "audio/wav"
    if data[:4] == b"OggS":
        return "audio/ogg"
    if data[:4] == b"fLaC":
        return "audio/flac"
    if data[:4] == b"\x1aE\xdf\xa3":
        return "audio/webm"
    return "audio/mpeg"


# ---------- Pages ----------

def _est_legend(est: dict) -> str:
    return t("mod_legend",
             img=est.get("image_count", 0),
             vid=est.get("video_count", 0),
             aud=est.get("audio_count", 0),
             mus=est.get("music_count", 0),
             txt=est.get("text_count", 0))


def page_dashboard():
    st.header(f"🏠 {t('page_dashboard')}")
    projects = list_projects()
    idx = load_index()

    cols = st.columns(4)
    cols[0].metric(t("metric_projects"), len(projects))
    if idx:
        cols[1].metric(t("metric_total_resources"), idx.get("total_resources", 0))
        mod = idx.get("resources_by_modality", {})
        cols[2].metric(t("metric_images"), mod.get("image", 0))
        cols[3].metric(t("metric_music"), mod.get("music", 0))
    else:
        cols[1].metric(t("metric_total_resources"), t("metric_dash"))
        cols[2].metric(t("metric_images"), t("metric_dash"))
        cols[3].metric(t("metric_music"), t("metric_dash"))

    st.divider()
    st.subheader(f"📁 {t('projects_list')}")
    if not projects:
        st.info(t("no_projects_yet"))
        return

    for proj in projects:
        with st.container(border=True):
            name = proj["name"]
            plan = proj["plan"]
            report = proj["report"]
            c1, c2, c3 = st.columns([3, 2, 2])
            with c1:
                st.markdown(f"### 🎮 {name}")
                art = plan.get("style_guide", {}).get("art_style", "?")[:40]
                ptype = plan.get("project_type", "?")
                st.caption(f"{t('project_type')}: {ptype} · {t('project_art_style')}: {art}")
            with c2:
                est = plan.get("total_estimate", {})
                st.markdown(f"**{t('estimated_resources')}**")
                st.caption(_est_legend(est))
            with c3:
                if report:
                    st.markdown(f"**{t('latest_generation')}**")
                    st.caption(t("gen_summary",
                                  ok=report.get("success", 0),
                                  fail=report.get("failed", 0),
                                  skip=report.get("skipped", 0)))
                else:
                    st.caption(t("no_generation_yet"))


def page_doctor():
    st.header(f"🔍 {t('page_doctor')}")
    st.caption(t("doctor_caption"))
    if st.button(t("doctor_run_btn"), type="primary"):
        with st.spinner(t("doctor_spinner")):
            code, _ = run_script("doctor.py", [])
        if code == 0:
            st.success(f"✅ {t('doctor_done_ok')}")
        else:
            st.error(f"❌ {t('doctor_done_err', code=code)}")


def page_plan():
    st.header(f"🧠 {t('page_plan')}")
    st.caption(t("plan_caption"))

    col1, col2 = st.columns([3, 1])
    with col1:
        uploaded = st.file_uploader(t("plan_upload"), type=["md", "txt"])
    with col2:
        st.write("")
        st.write("")
        use_template = st.button(t("plan_use_template_btn"))

    design_text = ""
    if uploaded:
        design_text = uploaded.read().decode("utf-8")
    elif use_template and (BASE_DIR / "design.md").exists():
        design_text = (BASE_DIR / "design.md").read_text(encoding="utf-8")
        st.info(t("plan_loaded_info", path=str(BASE_DIR / "design.md"), n=len(design_text)))

    if design_text:
        st.text_area(t("plan_preview_label"), design_text, height=200, disabled=True)

        if st.button(t("plan_run_btn"), type="primary"):
            tmp = BASE_DIR / "design_input.md"
            tmp.write_text(design_text, encoding="utf-8")
            with st.spinner(t("plan_spinner")):
                code, _ = run_script("plan.py", [str(tmp.relative_to(BASE_DIR))])
            if code == 0:
                st.success(f"✅ {t('plan_done_ok')}")
                load_plan.clear()
            else:
                st.error(f"❌ {t('doctor_done_err', code=code)}")

    st.divider()
    st.subheader(t("plan_existing_projects"))
    projects = list_projects()
    if not projects:
        st.caption(t("plan_no_projects"))
        return
    for p in projects:
        st.caption(f"• {p['name']}  ({len(p['plan'].get('resources', []))} resource groups)")


def page_generate():
    st.header(f"⚙️ {t('page_generate')}")
    st.caption(t("generate_caption"))

    projects = list_projects()
    if not projects:
        st.warning(t("generate_no_projects"))
        return

    project = st.selectbox(t("generate_select_project"), [p["name"] for p in projects])
    if not project:
        return

    plan = load_plan(project)
    if plan:
        est = plan.get("total_estimate", {})
        st.caption(f"{t('generate_estimate_prefix')} {_est_legend(est)}")

    col1, col2, col3 = st.columns(3)
    with col1:
        skip = st.multiselect(t("generate_skip_label"), ["image", "video", "audio", "music", "text"])
    with col2:
        force = st.checkbox(t("generate_force_label"), value=False)
    with col3:
        st.write("")
        st.write("")
        run_btn = st.button(t("generate_run_btn"), type="primary")

    if run_btn:
        args = [project]
        if skip:
            args.extend(["--skip", *skip])
        if force:
            args.append("--force")
        with st.spinner(t("generate_spinner")):
            code, _ = run_script("generate.py", args)
        if code == 0:
            st.success(f"✅ {t('generate_done_ok')}")
        else:
            st.error(f"❌ {t('generate_done_err', code=code)}")
        load_index.clear()

    st.divider()
    st.subheader(t("generate_latest_report"))
    proj = next((p for p in projects if p["name"] == project), None)
    if proj and proj["report"]:
        r = proj["report"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(t("metric_total"), r.get("total", 0))
        c2.metric(t("metric_success"), r.get("success", 0))
        c3.metric(t("metric_skipped"), r.get("skipped", 0))
        c4.metric(t("metric_failed"), r.get("failed", 0))

        if r.get("results"):
            rows = []
            for x in r["results"]:
                rows.append({
                    t("col_status"): {"success": "✅", "skipped": "⏭️", "failed": "❌"}.get(x.get("status"), "?"),
                    t("col_modality"): x.get("modality"),
                    t("col_resource"): x.get("resource_name"),
                    t("col_filename"): x.get("filename"),
                })
            st.dataframe(rows, use_container_width=True, hide_index=True)


def page_library():
    st.header(f"📚 {t('page_library')}")
    st.caption(t("library_caption"))

    idx = load_index()
    if not idx:
        st.warning(t("library_no_index"))
        if st.button(t("library_rebuild_btn")):
            with st.spinner(t("library_rebuild_spinner")):
                code, _ = run_script("index.py", ["--rebuild"])
            if code == 0:
                st.success(f"✅ {t('library_rebuild_ok')}")
                load_index.clear()
        return

    catalog = idx.get("global_catalog", [])
    if not catalog:
        st.info(t("library_no_resources"))
        return

    c1, c2, c3 = st.columns([3, 1, 1])
    with c1:
        query = st.text_input(t("library_search_placeholder"), "")
    with c2:
        categories = sorted({r["category"] for r in catalog})
        cat = st.selectbox(t("library_category"), [t("library_filter_all")] + categories)
    with c3:
        modalities = sorted({r["modality"] for r in catalog if r["modality"] != "unknown"})
        mod = st.selectbox(t("library_modality"), [t("library_filter_all")] + modalities)

    all_label = t("library_filter_all")
    q = query.lower()
    results = []
    for r in catalog:
        if cat != all_label and r["category"] != cat:
            continue
        if mod != all_label and r["modality"] != mod:
            continue
        if q:
            hay = " ".join([
                r.get("name", ""), r.get("display_name", ""),
                r.get("description", ""), r.get("resource_id", ""),
                r.get("project", ""),
            ]).lower()
            if q not in hay:
                continue
        results.append(r)

    st.caption(t("library_match_count", n=len(results), total=len(catalog)))
    st.divider()

    cols_per_row = 3
    for i in range(0, min(len(results), 60), cols_per_row):
        row = results[i:i + cols_per_row]
        cols = st.columns(cols_per_row)
        for col, r in zip(cols, row):
            with col:
                with st.container(border=True):
                    name = r.get("display_name") or r["name"]
                    st.markdown(f"**[{r['modality']}] {name}**")
                    st.caption(f"📁 {r['project']} / {r['category']}")
                    if r.get("description"):
                        st.caption(f"📝 {r['description']}")
                    st.caption(f"📄 {r['filename']}")

                    path = BASE_DIR / r["path"]
                    if r["modality"] == "image":
                        if path.exists():
                            try:
                                st.image(str(path), use_container_width=True)
                            except Exception:
                                pass
                    elif r["modality"] in ("audio", "music"):
                        if path.exists():
                            try:
                                data = path.read_bytes()
                                st.audio(data, format=detect_audio_mime(data))
                            except Exception as e:
                                st.caption(t("library_audio_fail", e=e))
                    elif r["modality"] == "video":
                        if path.exists():
                            try:
                                st.video(str(path))
                            except Exception as e:
                                st.caption(t("library_video_fail", e=e))
                    elif r["modality"] == "text":
                        if path.exists():
                            try:
                                txt = path.read_text(encoding="utf-8", errors="replace")
                                st.text(txt[:400] + ("…" if len(txt) > 400 else ""))
                            except Exception:
                                pass

                    with st.popover(t("library_reuse_popover")):
                        target = st.text_input(t("library_reuse_target"), key=f"reuse_{r['id']}")
                        if st.button(t("library_reuse_btn"), key=f"do_{r['id']}") and target:
                            src = BASE_DIR / r["path"]
                            tgt_dir = PROJECTS_DIR / safe_name(target) / r["category"]
                            tgt_dir.mkdir(parents=True, exist_ok=True)
                            tgt_path = tgt_dir / r["filename"]
                            shutil.copy2(src, tgt_path)
                            st.success(t("library_reuse_done", path=str(tgt_path.relative_to(BASE_DIR))))


# ---------- Sidebar ----------

# Stable page IDs paired with their i18n keys. The ID is the routing key,
# the i18n key provides the display label.
PAGES = [
    ("dashboard", "nav_dashboard"),
    ("doctor",    "nav_doctor"),
    ("plan",      "nav_plan"),
    ("generate",  "nav_generate"),
    ("library",   "nav_library"),
]

language_picker()

page_id = st.sidebar.radio(
    t("nav_label"),
    options=[pid for pid, _ in PAGES],
    format_func=lambda pid: t(dict(PAGES)[pid]),
)

st.sidebar.divider()
st.sidebar.caption(
    f"📂 {t('sidebar_project_root')}: `{BASE_DIR.name}`\n\n"
    f"🐍 {t('sidebar_python')}: `{sys.version_info.major}.{sys.version_info.minor}`\n\n"
    f"📦 {t('sidebar_streamlit')}: `1.58.0`"
)

if page_id == "dashboard":
    page_dashboard()
elif page_id == "doctor":
    page_doctor()
elif page_id == "plan":
    page_plan()
elif page_id == "generate":
    page_generate()
elif page_id == "library":
    page_library()
