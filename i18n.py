"""
Minimal i18n for the Streamlit UI.
Usage:
    from i18n import t, LANGS, get_lang, set_lang
    st.write(t("dashboard_title"))

Add a new language by adding a key to LANGS.
Add a new string by adding it to every language dict.
Missing keys fall back to the key itself (visible in UI for easy spotting).
"""
from typing import Callable

LANGS: dict[str, dict[str, str]] = {
    "en": {
        # --- Sidebar ---
        "nav_label": "Navigation",
        "nav_dashboard": "Home",
        "nav_doctor": "Doctor",
        "nav_plan": "Plan",
        "nav_generate": "Generate",
        "nav_library": "Library",
        "sidebar_project_root": "Project root",
        "sidebar_python": "Python",
        "sidebar_streamlit": "Streamlit",
        "sidebar_language": "Language",

        # --- Page titles ---
        "page_dashboard": "Project Overview",
        "page_doctor": "API Diagnostics",
        "page_plan": "Resource Planning",
        "page_generate": "Resource Generation",
        "page_library": "Resource Library",

        # --- Dashboard ---
        "metric_projects": "Projects",
        "metric_total_resources": "Total resources",
        "metric_images": "Images",
        "metric_music": "Music",
        "metric_dash": "—",
        "projects_list": "Projects",
        "no_projects_yet": "No projects yet. Click **🧠 Plan** above to create one.",
        "project_type": "Type",
        "project_art_style": "Art style",
        "estimated_resources": "Estimated resources",
        "latest_generation": "Latest generation",
        "no_generation_yet": "Not yet generated",
        "gen_summary": "✅ {ok} failed {fail} skipped {skip}",

        # --- Doctor ---
        "doctor_caption": "One-click test of M3 / image / video / TTS / music API connectivity.",
        "doctor_run_btn": "Run doctor.py",
        "doctor_spinner": "Testing all APIs (video may take up to 3 min)...",
        "doctor_done_ok": "Diagnostics complete",
        "doctor_done_err": "Process exited with code {code}",

        # --- Plan ---
        "plan_caption": "Upload a game design document → M3 breaks it into a generation plan.",
        "plan_upload": "Upload design document (.md / .txt)",
        "plan_use_template_btn": "Use project-root design.md",
        "plan_loaded_info": "Loaded {path} ({n} chars)",
        "plan_preview_label": "Design document preview",
        "plan_run_btn": "Run plan.py (overwrites existing plan.json)",
        "plan_spinner": "M3 is analyzing (4-8 min)...",
        "plan_done_ok": "Planning complete! Check **📚 Library** or **🏠 Home** above.",
        "plan_existing_projects": "Existing projects",
        "plan_no_projects": "No projects yet.",

        # --- Generate ---
        "generate_caption": "Batch-generate resources from plan.json via API.",
        "generate_no_projects": "No projects yet. Go to **🧠 Plan** to create one.",
        "generate_select_project": "Select project",
        "generate_estimate_prefix": "Estimate:",
        "generate_skip_label": "Skip modalities",
        "generate_force_label": "Force re-generation (--force)",
        "generate_run_btn": "Run generate.py",
        "generate_spinner": "Generating... report appears below when done",
        "generate_done_ok": "Generation complete",
        "generate_done_err": "Process exited with code {code}",
        "generate_latest_report": "Latest generation report",
        "metric_total": "Total",
        "metric_success": "Success",
        "metric_skipped": "Skipped",
        "metric_failed": "Failed",
        "col_status": "Status",
        "col_modality": "Modality",
        "col_resource": "Resource",
        "col_filename": "File",

        # --- Library ---
        "library_caption": "Search, filter, preview and reuse resources across all projects.",
        "library_no_index": "No index yet. Either run `python scripts/index.py --rebuild` in a terminal, or generate something to build it automatically.",
        "library_rebuild_btn": "Rebuild index",
        "library_rebuild_spinner": "Scanning all projects...",
        "library_rebuild_ok": "Index updated",
        "library_no_resources": "No resources yet.",
        "library_search_placeholder": "Search (Chinese name / English filename / description / ID / project)",
        "library_category": "Category",
        "library_modality": "Modality",
        "library_filter_all": "All",
        "library_match_count": "Showing {n} / {total} resources",
        "library_uncategorized": "Uncategorized",
        "library_audio_fail": "Audio playback failed: {e}",
        "library_video_fail": "Video playback failed: {e}",
        "library_reuse_popover": "Reuse...",
        "library_reuse_target": "Target project name",
        "library_reuse_btn": "Copy",
        "library_reuse_done": "Copied to {path}",

        # --- Modality emoji legend ---
        "mod_legend": "{img} image · {vid} video · {aud} audio · {mus} music · {txt} text",
    },
    "zh": {
        # --- Sidebar ---
        "nav_label": "导航",
        "nav_dashboard": "🏠 概览",
        "nav_doctor": "🔍 诊断",
        "nav_plan": "🧠 规划",
        "nav_generate": "⚙️ 生成",
        "nav_library": "📚 资源库",
        "sidebar_project_root": "项目根",
        "sidebar_python": "Python",
        "sidebar_streamlit": "Streamlit",
        "sidebar_language": "语言",

        # --- Page titles ---
        "page_dashboard": "项目概览",
        "page_doctor": "API 诊断",
        "page_plan": "资源规划",
        "page_generate": "资源生成",
        "page_library": "资源库",

        # --- Dashboard ---
        "metric_projects": "项目数",
        "metric_total_resources": "资源总数",
        "metric_images": "图像",
        "metric_music": "音乐",
        "metric_dash": "—",
        "projects_list": "项目列表",
        "no_projects_yet": "还没有项目。点上方 **🧠 规划** 创建一个。",
        "project_type": "类型",
        "project_art_style": "美术",
        "estimated_resources": "预计资源",
        "latest_generation": "最近生成",
        "no_generation_yet": "未生成",
        "gen_summary": "✅ {ok} 失败 {fail} 跳过 {skip}",

        # --- Doctor ---
        "doctor_caption": "一键测试 M3 / 图像 / 视频 / TTS / 音乐 API 连通性。",
        "doctor_run_btn": "运行 doctor.py",
        "doctor_spinner": "正在测试所有 API（视频最长 ~3 分钟）...",
        "doctor_done_ok": "诊断完成",
        "doctor_done_err": "进程退出码 {code}",

        # --- Plan ---
        "plan_caption": "上传游戏设计文档 → M3 拆解成可生成的资源清单。",
        "plan_upload": "上传设计文档 (.md / .txt)",
        "plan_use_template_btn": "用项目根 design.md",
        "plan_loaded_info": "已加载 {path} ({n} 字符)",
        "plan_preview_label": "设计文档预览",
        "plan_run_btn": "运行 plan.py（覆盖现有 plan.json）",
        "plan_spinner": "M3 正在分析（4-8 分钟）...",
        "plan_done_ok": "规划完成！点上方 **📚 资源库** 或 **🏠 概览** 查看。",
        "plan_existing_projects": "已有项目",
        "plan_no_projects": "还没有项目。",

        # --- Generate ---
        "generate_caption": "按 plan.json 批量调用 API 生成资源。",
        "generate_no_projects": "还没有项目。先去 **🧠 规划** 创建一个。",
        "generate_select_project": "选择项目",
        "generate_estimate_prefix": "预计:",
        "generate_skip_label": "跳过模态",
        "generate_force_label": "强制重新生成 (--force)",
        "generate_run_btn": "运行 generate.py",
        "generate_spinner": "生成中... 完成后下方会显示报告",
        "generate_done_ok": "生成完成",
        "generate_done_err": "进程退出码 {code}",
        "generate_latest_report": "最近生成报告",
        "metric_total": "总数",
        "metric_success": "成功",
        "metric_skipped": "跳过",
        "metric_failed": "失败",
        "col_status": "状态",
        "col_modality": "模态",
        "col_resource": "资源",
        "col_filename": "文件",

        # --- Library ---
        "library_caption": "搜索/筛选/预览/复用所有项目的资源。",
        "library_no_index": "索引还没建。先在命令行跑 `python scripts/index.py --rebuild`，或生成过项目后会自动建。",
        "library_rebuild_btn": "重建索引",
        "library_rebuild_spinner": "扫描所有项目...",
        "library_rebuild_ok": "索引已更新",
        "library_no_resources": "还没有资源。",
        "library_search_placeholder": "搜索（中文名/英文文件名/描述/ID/项目名）",
        "library_category": "分类",
        "library_modality": "模态",
        "library_filter_all": "全部",
        "library_match_count": "匹配 {n} / {total} 个资源",
        "library_uncategorized": "未分类",
        "library_audio_fail": "⚠️ 播放失败: {e}",
        "library_video_fail": "⚠️ 播放失败: {e}",
        "library_reuse_popover": "复用...",
        "library_reuse_target": "目标项目名",
        "library_reuse_btn": "复制",
        "library_reuse_done": "已复制到 {path}",

        # --- Modality emoji legend ---
        "mod_legend": "{img} 图像 · {vid} 视频 · {aud} 音频 · {mus} 音乐 · {txt} 文本",
    },
}

DEFAULT_LANG = "en"


def get_lang() -> str:
    """Get current language from session state, falling back to default."""
    import streamlit as st
    return st.session_state.get("lang", DEFAULT_LANG)


def set_lang(lang: str) -> None:
    """Set current language in session state."""
    import streamlit as st
    st.session_state["lang"] = lang


def t(key: str, **kwargs) -> str:
    """Translate a key, with optional format kwargs. Falls back to the key on miss."""
    lang = get_lang()
    msg = LANGS.get(lang, LANGS[DEFAULT_LANG]).get(key)
    if msg is None:
        return key
    if kwargs:
        try:
            return msg.format(**kwargs)
        except (KeyError, IndexError):
            return msg
    return msg


def language_picker() -> None:
    """Render the language picker in the sidebar. Call from app.py."""
    import streamlit as st
    with st.sidebar:
        current = get_lang()
        labels = {"en": "English", "zh": "中文"}
        options = list(labels.keys())
        idx = options.index(current) if current in options else 0
        choice = st.selectbox(
            t("sidebar_language"),
            options,
            index=idx,
            format_func=lambda x: labels[x],
            key="lang_picker",
        )
        if choice != current:
            set_lang(choice)
            st.rerun()
