#!/usr/bin/env python3
"""
MiniMax 诊断工具 - 测试所有 API 连通性
对齐 wx_project/minimax_test 验证过的接口
"""
import json
import sys
import time
from pathlib import Path
import requests

BASE_DIR = Path(__file__).parent.parent
CONFIG_PATH = BASE_DIR / "config" / "minimax.json"


class MiniMaxClient:
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


def test_m3(client):
    """测试 M3 文本 API: POST /v1/chat/completions"""
    print("  📝 测试 M3 文本...", end=" ")
    try:
        resp = client.post("/v1/chat/completions", {
            "model": "MiniMax-M3",
            "messages": [{"role": "user", "content": "你好，请回复'测试成功'"}],
            "max_tokens": 50,
        }, timeout=30)
        content = resp["choices"][0]["message"]["content"]
        print(f"✅ OK - 回复: {content[:30]}")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_image(client):
    """测试图像 API: POST /v1/image_generation"""
    print("  🖼️ 测试图像生成...", end=" ")
    try:
        resp = client.post("/v1/image_generation", {
            "model": "image-01",
            "prompt": "a simple red apple on white background",
            "n": 1,
            "response_format": "url",
            "prompt_optimizer": True,
            "aspect_ratio": "1:1",
        }, timeout=120)
        data = resp.get("data") or {}
        urls = data.get("image_urls")
        if urls and len(urls) > 0:
            print(f"✅ OK - URL: {urls[0][:50]}...")
            return True
        raise RuntimeError(f"无 image_urls: {resp}")
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_video(client):
    """测试视频 API: POST /v1/video_generation + 轮询"""
    print("  🎬 测试视频生成...", end=" ")
    try:
        resp = client.post("/v1/video_generation", {
            "model": "MiniMax-Hailuo-2.3",
            "prompt": "a cat walking on grass",
            "duration": 6,
            "resolution": "768P",
            "prompt_optimizer": True,
        }, timeout=60)
        task_id = resp.get("task_id")
        if not task_id:
            raise RuntimeError(f"无 task_id: {resp}")
        
        # 轮询 (最多3分钟)
        for _ in range(22):  # 22 * 8s = 176s
            time.sleep(8)
            status_resp = client.get("/v1/query/video_generation", {"task_id": task_id})
            status = (status_resp.get("status") or "").lower()
            if status == "success":
                file_id = status_resp.get("file_id")
                if file_id:
                    print(f"✅ OK - task_id: {task_id}, file_id: {file_id}")
                    return True
                raise RuntimeError(f"无 file_id")
            elif status == "fail":
                raise RuntimeError(f"任务失败: {status_resp}")
        raise TimeoutError(f"视频任务轮询超时: {task_id}")
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_tts(client):
    """测试 TTS API: POST /v1/t2a_v2"""
    print("  🎙️ 测试 TTS...", end=" ")
    try:
        resp = client.post("/v1/t2a_v2", {
            "model": "speech-2.6-hd",
            "text": "你好，这是语音测试",
            "stream": False,
            "output_format": "hex",
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
        }, timeout=60)
        data = resp.get("data") or {}
        if data.get("audio") or data.get("audio_url"):
            print(f"✅ OK")
            return True
        raise RuntimeError(f"无音频数据: {resp}")
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_music(client):
    """测试音乐 API: POST /v1/music_generation"""
    print("  🎵 测试音乐生成...", end=" ")
    try:
        resp = client.post("/v1/music_generation", {
            "model": "music-2.6",
            "prompt": "relaxing piano music",
            "is_instrumental": True,
            "stream": False,
            "output_format": "hex",
            "audio_setting": {
                "sample_rate": 44100,
                "bitrate": 256000,
                "format": "mp3",
            },
        }, timeout=120)
        data = resp.get("data") or {}
        if data.get("audio"):
            print(f"✅ OK")
            return True
        raise RuntimeError(f"无音频数据: {resp}")
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def main():
    if not CONFIG_PATH.exists():
        print(f"❌ 配置文件不存在: {CONFIG_PATH}")
        print("   请检查 config/minimax.json 是否存在")
        sys.exit(1)
    
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    base_url = config["api_base"]
    api_key = config["api_key"]
    payg_key = config.get("payg_api_key", "") or api_key
    
    print("=" * 50)
    print("🔍 MiniMax API 诊断工具")
    print("=" * 50)
    print(f"📡 API Base: {base_url}")
    print(f"🔑 API Key: {'*' * 20} (已隐藏)")
    print()
    
    # 测试 Token Plan Key (图像/视频/tts/音乐)
    client = MiniMaxClient(api_key, base_url)
    results = []
    
    print("🎯 测试 Token Plan Key (api_key):")
    results.append(("图像(image-01)", test_image(client)))
    results.append(("视频(MiniMax-Hailuo-2.3)", test_video(client)))
    results.append(("TTS(speech-2.6-hd)", test_tts(client)))
    results.append(("音乐(music-2.6)", test_music(client)))
    
    # 测试 M3 (按量计费 Key)
    print()
    print("🎯 测试 M3 文本 (使用 payg_api_key):")
    text_client = MiniMaxClient(payg_key, base_url)
    results.append(("文本(MiniMax-M3)", test_m3(text_client)))
    
    # 汇总
    print()
    print("=" * 50)
    print("📊 诊断结果汇总")
    print("=" * 50)
    
    success = 0
    for name, ok in results:
        icon = "✅" if ok else "❌"
        print(f"  {icon} {name}")
        if ok:
            success += 1
    
    print()
    if success == len(results):
        print(f"🎉 所有 {len(results)} 项测试全部通过！")
        print("   可以开始运行: python scripts/generate.py <项目名>")
    else:
        print(f"⚠️ 通过 {success}/{len(results)} 项")
        print("   请检查 API Key 和额度是否正确")


if __name__ == "__main__":
    main()
