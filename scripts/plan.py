#!/usr/bin/env python3
"""
用 MiniMax M3 生成游戏资源生产计划
"""
import json
import os
import re
import sys
import time
import requests
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
CONFIG_PATH = BASE_DIR / "config" / "minimax.json"
PROMPT_PATH = BASE_DIR / "prompts" / "resource-planner.md"
OUTPUT_DIR = BASE_DIR / "assets" / "projects"


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_planner_prompt():
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def generate_plan(game_design_doc: str, config: dict) -> dict:
    """调用 M3 生成资源计划"""
    system_prompt = load_planner_prompt()
    
    # M3 文本调用按量计费 Key
    api_key = config.get("payg_api_key", "") or config["api_key"]
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": config["models"]["text"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请根据以下游戏设计文档，生成详细的资源生产计划：\n\n{game_design_doc}"}
        ],
        "temperature": 0.3,
        "max_tokens": 16000,
        "response_format": {"type": "json_object"},
    }
    
    retry_times = config.get("retry_times", 3)
    last_err = None
    for attempt in range(1, retry_times + 1):
        try:
            response = requests.post(
                f"{config['api_base']}/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=300
            )
            response.raise_for_status()
            break
        except Exception as e:
            last_err = e
            print(f"   ⚠️ 第 {attempt}/{retry_times} 次失败: {e}")
            if attempt < retry_times:
                time.sleep(min(2 ** attempt, 10))
    else:
        raise RuntimeError(f"M3 调用失败，已重试 {retry_times} 次: {last_err}")
    
    result = response.json()
    finish_reason = result["choices"][0].get("finish_reason")
    content = result["choices"][0]["message"]["content"]

    # 去掉 M3 的 <think>...</think> 思考块（如果有）
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)

    # 提取 JSON
    # M3 可能会在 JSON 外面包 markdown 代码块
    content = content.strip()
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()

    if finish_reason == "length":
        raise RuntimeError(
            f"M3 输出被截断 (max_tokens 用尽)，请增大 max_tokens 或精简设计文档"
        )

    plan = json.loads(content)
    return plan


def save_plan(plan: dict, project_name: str):
    """保存资源计划到项目目录"""
    safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in project_name)
    project_dir = OUTPUT_DIR / safe_name
    project_dir.mkdir(parents=True, exist_ok=True)
    
    plan_path = project_dir / "plan.json"
    with open(plan_path, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)
    
    # 创建资源子目录
    categories = set(r["category"] for r in plan.get("resources", []))
    for cat in categories:
        (project_dir / cat).mkdir(exist_ok=True)
    
    print(f"✅ 资源计划已保存: {plan_path}")
    print(f"📁 项目目录: {project_dir}")
    print(f"📊 预计生成:")
    est = plan.get("total_estimate", {})
    print(f"   图像: {est.get('image_count', 0)}")
    print(f"   视频: {est.get('video_count', 0)}")
    print(f"   音频: {est.get('audio_count', 0)}")
    print(f"   音乐: {est.get('music_count', 0)}")
    print(f"   文本: {est.get('text_count', 0)}")
    
    return project_dir


def main():
    if len(sys.argv) < 2:
        print("用法: python plan.py <游戏设计文档路径>")
        print("或: echo '你的游戏设计' | python plan.py -")
        sys.exit(1)
    
    config = load_config()
    
    if sys.argv[1] == "-":
        game_doc = sys.stdin.read()
    else:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            game_doc = f.read()
    
    print("🧠 正在用 M3 分析游戏设计文档...")
    plan = generate_plan(game_doc, config)
    
    project_name = plan.get("project_name", "untitled")
    save_plan(plan, project_name)


if __name__ == "__main__":
    main()
