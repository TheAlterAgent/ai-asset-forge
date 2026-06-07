#!/usr/bin/env python3
"""
根据 plan.json 调用 MiniMax 原生 API 生成资源
参考: wx_project/minimax_test 验证过的接口
"""
import json
import os
import sys
import time
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = Path(__file__).parent.parent
CONFIG_PATH = BASE_DIR / "config" / "minimax.json"
OUTPUT_DIR = BASE_DIR / "assets" / "projects"

_KNOWN_EXTS = {
    "png", "jpg", "jpeg", "webp", "gif", "bmp", "tga",
    "mp4", "mov", "avi", "webm", "mkv",
    "mp3", "wav", "ogg", "m4a", "flac",
    "txt",
}


def _parse_duration(value) -> float | None:
    """从 specs.duration 字符串里提取秒数，例如 '2秒' / '0.4s' / '120'"""
    if value is None:
        return None
    import re
    m = re.search(r"(\d+(?:\.\d+)?)", str(value))
    return float(m.group(1)) if m else None


def _smart_trim_audio(data: bytes, max_seconds: float) -> bytes:
    """智能裁剪 SFX：
    1) silencedetect 找自然静音起点（在 max_seconds 内）
    2) 目标时长 = min(自然结束 + 0.15s 余音, max_seconds)
    3) 加 0.2s 淡出 + 重编码 128k（即使在静音里也加，避免硬切"砰"声）
    失败则回退到原数据。
    """
    import re
    try:
        import imageio_ffmpeg
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        import subprocess

        # Step 1: silencedetect 找自然静音点
        proc = subprocess.run(
            [ffmpeg, "-y", "-loglevel", "info",
             "-i", "pipe:0",
             "-t", str(max_seconds),
             "-af", "silencedetect=noise=-30dB:d=0.3",
             "-f", "null", "-"],
            input=data, capture_output=True, timeout=60,
        )
        natural_end = None
        for line in proc.stderr.decode(errors="replace").splitlines():
            m = re.search(r"silence_start: (\d+\.?\d*)", line)
            if m:
                t = float(m.group(1))
                if t < max_seconds:
                    natural_end = t  # 取最后一个（最晚的）silence_start
                    # 不 break，继续找更晚的

        # Step 2: 计算目标裁剪点
        if natural_end is not None and natural_end < max_seconds * 0.8:
            # 自然结束点明显早于 max，裁到自然结束 + 0.15s 余音
            trim_to = min(natural_end + 0.15, max_seconds)
            strategy = f"自然结束@{natural_end:.2f}s"
        else:
            # 没找到明显的静音点（声音一直持续），按 max_seconds 裁
            trim_to = max_seconds
            strategy = f"按上限{max_seconds}s"

        # Step 3: 始终加 0.2s 淡出，重编码 128k
        fade_start = max(0.0, trim_to - 0.2)
        proc = subprocess.run(
            [ffmpeg, "-y", "-loglevel", "error",
             "-i", "pipe:0",
             "-t", str(trim_to),
             "-af", f"afade=t=out:st={fade_start}:d=0.2",
             "-ac", "2", "-ar", "44100", "-b:a", "128k",
             "-f", "mp3", "pipe:1"],
            input=data, capture_output=True, timeout=60,
        )
        if proc.returncode == 0 and proc.stdout:
            return proc.stdout
    except Exception as e:
        print(f"   ⚠️ ffmpeg 智能裁剪失败: {e}")
    return data


def _resolve_music_duration(asset: dict, category: str) -> float | None:
    """从 specs.duration 推断秒数；找不到时按 category 给默认。返回 None = 不裁剪（BGM 默认）"""
    seconds = _parse_duration(asset.get("specs", {}).get("duration"))
    if seconds is not None:
        return seconds
    defaults = {
        "sfx": 2.0,
        "skill": 2.0,
        "ui": 1.5,
        "scene": 30.0,
    }
    return defaults.get(category)


def _normalize_ext(format_field, default: str) -> str:
    """从 M3 写脏的 specs.format 里提取有效后缀，比如 'PNG透明背景' → 'png'"""
    if not format_field:
        return default
    first = str(format_field).strip().split()[0].lstrip(".").lower()
    if first in _KNOWN_EXTS:
        return "jpg" if first == "jpeg" else first
    return default


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


class MiniMaxClient:
    """对齐 wx_project/minimax_test/minimax_client.py 的实现"""
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })

    def _url(self, path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return f"{self.base_url}{path}"

    def post(self, path: str, json_data: dict = None, timeout: int = 60):
        resp = self.session.post(self._url(path), json=json_data or {}, timeout=timeout)
        resp.raise_for_status()
        return resp.json()

    def get(self, path: str, params: dict = None, timeout: int = 60):
        resp = self.session.get(self._url(path), params=params or {}, timeout=timeout)
        resp.raise_for_status()
        return resp.json()

    def download(self, url: str, save_path: str, timeout: int = 300) -> str:
        with requests.get(url, stream=True, timeout=timeout) as r:
            r.raise_for_status()
            with open(save_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        return save_path


def generate_image(prompt: str, config: dict, client: MiniMaxClient, save_path: Path) -> bool:
    """调用 MiniMax 图像生成 API: POST /v1/image_generation"""
    try:
        payload = {
            "model": config["models"]["image"],
            "prompt": prompt,
            "n": 1,
            "response_format": "url",
            "prompt_optimizer": True,
            "aspect_ratio": "1:1",
        }
        resp = client.post("/v1/image_generation", payload, timeout=300)
        data = resp.get("data") or {}
        image_urls = data.get("image_urls")
        if image_urls and len(image_urls) > 0:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            client.download(image_urls[0], str(save_path))
            return True
        raise RuntimeError(f"响应中无图片URL: {resp}")
    except Exception as e:
        print(f"   ❌ 图像生成失败: {e}")
        return False


def generate_video(prompt: str, config: dict, client: MiniMaxClient, save_path: Path) -> bool:
    """调用 MiniMax 视频生成 API: POST /v1/video_generation + 轮询"""
    try:
        payload = {
            "model": config["models"]["video"],
            "prompt": prompt,
            "duration": 6,
            "resolution": "768P",
            "prompt_optimizer": True,
        }
        resp = client.post("/v1/video_generation", payload, timeout=60)
        task_id = resp.get("task_id")
        if not task_id:
            raise RuntimeError(f"提交失败: {resp}")

        # 轮询
        deadline = time.time() + 1800
        while time.time() < deadline:
            time.sleep(8)
            status_resp = client.get("/v1/query/video_generation", {"task_id": task_id})
            status = (status_resp.get("status") or "").lower()
            if status in {"success"}:
                file_id = status_resp.get("file_id")
                if not file_id:
                    raise RuntimeError(f"任务完成但无 file_id: {status_resp}")
                file_resp = client.get("/v1/files/retrieve", {"file_id": file_id})
                download_url = (file_resp.get("file") or {}).get("download_url")
                if not download_url:
                    raise RuntimeError(f"无下载链接: {file_resp}")
                save_path.parent.mkdir(parents=True, exist_ok=True)
                client.download(download_url, str(save_path))
                return True
            elif status in {"fail"}:
                raise RuntimeError(f"视频生成失败: {status_resp}")
            print(f"   ... 视频任务 {task_id} 状态: {status}")
        raise TimeoutError(f"视频生成超时: {task_id}")
    except Exception as e:
        print(f"   ❌ 视频生成失败: {e}")
        return False


def generate_tts(text: str, config: dict, client: MiniMaxClient, save_path: Path) -> bool:
    """调用 MiniMax TTS API: POST /v1/t2a_v2"""
    try:
        payload = {
            "model": config["models"]["tts"],
            "text": text,
            "stream": False,
            "voice_setting": {
                "voice_id": "male-qn-qingse",
                "speed": 1.0,
                "vol": 1.0,
                "pitch": 0,
            },
            "audio_setting": {
                "sample_rate": 32000,
                "bitrate": 128000,
                "format": "mp3",
                "channel": 1,
            },
            "output_format": "hex",
        }
        resp = client.post("/v1/t2a_v2", payload, timeout=120)
        data = resp.get("data") or {}
        if data.get("audio"):
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_bytes(bytes.fromhex(data["audio"]))
            return True
        if data.get("audio_url"):
            save_path.parent.mkdir(parents=True, exist_ok=True)
            client.download(data["audio_url"], str(save_path))
            return True
        raise RuntimeError(f"响应中无音频数据: {resp}")
    except Exception as e:
        print(f"   ❌ TTS 生成失败: {e}")
        return False


def generate_music(prompt: str, config: dict, client: MiniMaxClient, save_path: Path, max_seconds: float | None = None) -> bool:
    """调用 MiniMax 音乐生成 API: POST /v1/music_generation
    max_seconds: 超过这个秒数会用 ffmpeg 裁剪（SFX 资源默认 2-3s）
    """
    try:
        payload = {
            "model": config["models"]["music"],
            "stream": False,
            "output_format": "hex",
            "audio_setting": {
                "sample_rate": 44100,
                "bitrate": 256000,
                "format": "mp3",
            },
        }
        if prompt:
            payload["prompt"] = prompt
        payload["is_instrumental"] = True

        resp = client.post("/v1/music_generation", payload, timeout=300)
        data = resp.get("data") or {}
        if data.get("audio"):
            audio_bytes = bytes.fromhex(data["audio"])
            if max_seconds:
                original = len(audio_bytes)
                audio_bytes = _smart_trim_audio(audio_bytes, max_seconds)
                if len(audio_bytes) < original:
                    print(f"   ✂️  {original//1024}KB → {len(audio_bytes)//1024}KB (≤{max_seconds}s, 智能)")
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_bytes(audio_bytes)
            return True
        raise RuntimeError(f"响应中无音频数据: {resp}")
    except Exception as e:
        print(f"   ❌ 音乐生成失败: {e}")
        return False


def _strip_think_tags(text: str) -> str:
    """去掉 M3 的 <think>...</think> 思考块（即使未闭合）"""
    import re
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    text = re.sub(r"<think>.*$", "", text, flags=re.DOTALL)
    text = text.strip()
    # 剥 markdown 围栏
    if text.startswith("```"):
        nl = text.find("\n")
        if nl > 0:
            text = text[nl+1:]
        if text.endswith("```"):
            text = text[:-3]
    return text.strip()


def generate_text(prompt: str, config: dict, client: MiniMaxClient) -> str:
    """调用 M3 文本 API: POST /v1/chat/completions"""
    payload = {
        "model": config["models"]["text"],
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 4000,
    }
    retry_times = config.get("retry_times", 3)
    last_err = None
    for attempt in range(1, retry_times + 1):
        try:
            resp = client.post("/v1/chat/completions", payload, timeout=120)
            return _strip_think_tags(resp["choices"][0]["message"]["content"])
        except Exception as e:
            last_err = e
            if attempt < retry_times:
                import time
                time.sleep(min(2 ** attempt, 10))
    print(f"   ❌ 文本生成失败（已重试 {retry_times} 次）: {last_err}")
    return ""


def process_asset(resource: dict, asset: dict, project_dir: Path, config: dict, client: MiniMaxClient, force: bool = False) -> dict:
    """处理单个资源文件"""
    modality = asset["modality"]
    filename = asset.get("filename", "unnamed")
    prompt = asset.get("prompt", "")
    prompt_zh = asset.get("prompt_zh", "")

    generation_prompt = prompt_zh if modality == "text" and prompt_zh else prompt

    category = resource["category"]
    save_dir = project_dir / category
    save_dir.mkdir(exist_ok=True)

    result = {
        "resource_id": resource["id"],
        "resource_name": resource["name"],
        "modality": modality,
        "filename": filename,
        "status": "failed",
        "path": ""
    }

    if modality == "image":
        ext = _normalize_ext(asset.get("specs", {}).get("format"), "png")
        save_path = save_dir / f"{filename}.{ext}"
    elif modality == "video":
        ext = _normalize_ext(asset.get("specs", {}).get("format"), "mp4")
        save_path = save_dir / f"{filename}.{ext}"
    elif modality == "audio":
        ext = _normalize_ext(asset.get("specs", {}).get("format"), "mp3")
        save_path = save_dir / f"{filename}.{ext}"
    elif modality == "music":
        ext = _normalize_ext(asset.get("specs", {}).get("format"), "mp3")
        save_path = save_dir / f"{filename}.{ext}"
    elif modality == "text":
        save_path = save_dir / f"{filename}.txt"
    else:
        return result

    if save_path.exists() and not force:
        result["status"] = "skipped"
        result["path"] = str(save_path.relative_to(BASE_DIR))
        return result

    if modality == "image":
        if generate_image(generation_prompt, config, client, save_path):
            result["status"] = "success"
            result["path"] = str(save_path.relative_to(BASE_DIR))

    elif modality == "video":
        if generate_video(generation_prompt, config, client, save_path):
            result["status"] = "success"
            result["path"] = str(save_path.relative_to(BASE_DIR))

    elif modality == "audio":
        # sfx/skill/ui/scene 类别的 audio 实际是音效描述，应走音乐 API (instrumental)
        # character/story 才是真正的语音，走 TTS
        if category in {"sfx", "skill", "ui", "scene"}:
            print(f"   ℹ️ {filename} 类别={category}，自动走音乐 API（音效）")
            max_sec = _resolve_music_duration(asset, category)
            if max_sec:
                print(f"   ⏱  目标时长 ≤{max_sec}s")
            if generate_music(generation_prompt, config, client, save_path, max_seconds=max_sec):
                result["status"] = "success"
                result["path"] = str(save_path.relative_to(BASE_DIR))
        else:
            if generate_tts(generation_prompt, config, client, save_path):
                result["status"] = "success"
                result["path"] = str(save_path.relative_to(BASE_DIR))

    elif modality == "sfx":
        # 显式 sfx 模态 = 走音乐 API 生成音效
        max_sec = _resolve_music_duration(asset, category)
        if max_sec:
            print(f"   ⏱  目标时长 ≤{max_sec}s")
        if generate_music(generation_prompt, config, client, save_path, max_seconds=max_sec):
            result["status"] = "success"
            result["path"] = str(save_path.relative_to(BASE_DIR))

    elif modality == "music":
        max_sec = _resolve_music_duration(asset, category)
        if max_sec:
            print(f"   ⏱  目标时长 ≤{max_sec}s")
        if generate_music(generation_prompt, config, client, save_path, max_seconds=max_sec):
            result["status"] = "success"
            result["path"] = str(save_path.relative_to(BASE_DIR))

    elif modality == "text":
        text_content = generate_text(generation_prompt, config, client)
        if text_content:
            save_path.write_text(text_content, encoding="utf-8")
            result["status"] = "success"
            result["path"] = str(save_path.relative_to(BASE_DIR))
            result["content"] = text_content[:200] + "..." if len(text_content) > 200 else text_content

    return result


def generate_project(project_name: str, config: dict, max_concurrent: int = 2, skip_modalities: set = None, force: bool = False):
    """根据 plan.json 生成所有资源"""
    if skip_modalities is None:
        skip_modalities = set()

    safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in project_name)
    project_dir = OUTPUT_DIR / safe_name
    plan_path = project_dir / "plan.json"
    
    if not plan_path.exists():
        print(f"❌ 项目计划不存在: {plan_path}")
        print(f"   先运行: python plan.py <你的游戏设计文档>")
        return
    
    with open(plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)
    
    resources = plan.get("resources", [])
    all_assets = []
    skipped = []
    for resource in resources:
        for asset in resource.get("assets", []):
            if asset.get("modality") in skip_modalities:
                skipped.append((resource, asset))
            else:
                all_assets.append((resource, asset))

    if skipped:
        skipped_names = {a["modality"] for _, a in skipped}
        print(f"⏭️  跳过 {len(skipped)} 个 {skipped_names} 资源")
    if force:
        print("🔁 --force 模式：已存在文件也会重新生成")
    
    print(f"🎮 项目: {plan.get('project_name', project_name)}")
    print(f"📊 总资源数: {len(all_assets)}")
    print(f"🔧 并发数: {max_concurrent}")
    print("-" * 50)
    
    # 创建 MiniMax 客户端
    # 图像/视频/音频/音乐用 api_key (Token Plan)
    # 文本(M3)用 payg_api_key (按量计费)，如果没有就用 api_key
    api_key = config["api_key"]
    text_key = config.get("payg_api_key", "") or api_key
    base_url = config["api_base"]
    
    client = MiniMaxClient(api_key, base_url)
    text_client = MiniMaxClient(text_key, base_url)
    
    results = []
    success_count = 0
    failed_count = 0
    skipped_count = 0
    
    # 注意：视频生成有轮询，并发不宜过高
    with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
        future_to_asset = {}
        for res, ast in all_assets:
            # 文本用 text_client，其他用 client
            use_client = text_client if ast["modality"] == "text" else client
            future = executor.submit(process_asset, res, ast, project_dir, config, use_client, force)
            future_to_asset[future] = (res, ast)
        
        for future in as_completed(future_to_asset):
            res, ast = future_to_asset[future]
            try:
                result = future.result()
                results.append(result)

                status = result["status"]
                icon = {"success": "✅", "skipped": "⏭️ ", "failed": "❌"}.get(status, "❓")
                print(f"{icon} [{result['modality']}] {result['resource_name']} - {result['filename']}")

                if status == "success":
                    success_count += 1
                elif status == "skipped":
                    skipped_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                print(f"❌ [{res['name']}] 处理异常: {e}")
                failed_count += 1
    
    # 保存生成报告
    report = {
        "project_name": plan.get("project_name", project_name),
        "total": len(all_assets),
        "success": success_count,
        "failed": failed_count,
        "skipped": skipped_count,
        "results": results
    }
    
    report_path = project_dir / "report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print("-" * 50)
    print(f"✅ 成功: {success_count} | ⏭️  跳过: {skipped_count} | ❌ 失败: {failed_count}")
    print(f"📄 报告已保存: {report_path}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="根据 plan.json 批量生成游戏资源")
    parser.add_argument("project", help="项目名称（对应 assets/projects/<name>/plan.json）")
    parser.add_argument("--skip", nargs="+", default=[], help="跳过的模态，可选: image video audio music text")
    parser.add_argument("--force", action="store_true", help="强制重新生成已存在的文件")
    args = parser.parse_args()

    config = load_config()
    max_concurrent = config.get("max_concurrent", 2)
    skip_modalities = set(args.skip)

    generate_project(args.project, config, max_concurrent, skip_modalities, args.force)


if __name__ == "__main__":
    main()
