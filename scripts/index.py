#!/usr/bin/env python3
"""
游戏资源库索引管理器
支持全局搜索、跨项目复用、标签管理
"""
import json
import hashlib
import shutil
from pathlib import Path
from datetime import datetime
from collections import defaultdict

BASE_DIR = Path(__file__).parent.parent
ASSETS_DIR = BASE_DIR / "assets"
PROJECTS_DIR = ASSETS_DIR / "projects"
INDEX_PATH = ASSETS_DIR / "index.json"


def compute_file_hash(filepath: Path) -> str:
    """计算文件 SHA256 哈希，用于去重"""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()[:16]


def scan_projects():
    """扫描所有项目的资源"""
    index = {
        "version": "1.0",
        "last_updated": datetime.now().isoformat(),
        "total_projects": 0,
        "total_resources": 0,
        "resources_by_modality": defaultdict(int),
        "projects": {},
        "global_catalog": [],
        "duplicates": []
    }
    
    hash_map = {}  # hash -> [resource_entries]
    
    for project_dir in PROJECTS_DIR.iterdir():
        if not project_dir.is_dir():
            continue
        
        plan_path = project_dir / "plan.json"
        report_path = project_dir / "report.json"

        if not plan_path.exists():
            continue

        with open(plan_path, "r", encoding="utf-8") as f:
            plan = json.load(f)

        # 从 plan.json 构建 (category, filename_stem) -> 元信息 的查找表
        asset_lookup = {}
        for res in plan.get("resources", []):
            cat = res.get("category")
            for asset in res.get("assets", []):
                stem = Path(asset.get("filename", "")).stem
                if cat and stem:
                    asset_lookup[(cat, stem)] = {
                        "resource_id": res.get("id", ""),
                        "display_name": res.get("name", ""),
                        "description": res.get("description", ""),
                        "modality": asset.get("modality", ""),
                    }

        project_name = plan.get("project_name", project_dir.name)
        project_entry = {
            "name": project_name,
            "type": plan.get("project_type", "unknown"),
            "style": plan.get("style_guide", {}),
            "path": str(project_dir.relative_to(BASE_DIR)),
            "resource_count": 0,
            "resources": []
        }
        
        # 遍历所有分类目录
        for category_dir in project_dir.iterdir():
            if not category_dir.is_dir() or category_dir.name in [".git"]:
                continue
            
            for asset_file in category_dir.iterdir():
                if asset_file.suffix in [".json", ".md"]:
                    continue
                
                file_hash = compute_file_hash(asset_file)
                modality = get_modality_from_ext(asset_file.suffix)

                meta = asset_lookup.get((category_dir.name, asset_file.stem), {})
                display_name = meta.get("display_name") or asset_file.stem
                description = meta.get("description", "")
                # 优先用 plan.json 里的 modality，避免 .mp3 分不清 music/audio
                plan_modality = meta.get("modality") or modality

                resource_entry = {
                    "id": f"{project_dir.name}_{category_dir.name}_{asset_file.stem}",
                    "resource_id": meta.get("resource_id", ""),
                    "project": project_name,
                    "category": category_dir.name,
                    "name": asset_file.stem,
                    "display_name": display_name,
                    "description": description,
                    "filename": asset_file.name,
                    "path": str(asset_file.relative_to(BASE_DIR)),
                    "modality": plan_modality,
                    "format": asset_file.suffix.lstrip("."),
                    "size_bytes": asset_file.stat().st_size,
                    "hash": file_hash,
                    "tags": infer_tags(asset_file.stem, category_dir.name, display_name, description)
                }
                
                project_entry["resources"].append(resource_entry)
                index["global_catalog"].append(resource_entry)
                index["resources_by_modality"][plan_modality] += 1
                
                # 检测重复
                if file_hash in hash_map:
                    index["duplicates"].append({
                        "hash": file_hash,
                        "files": [
                            hash_map[file_hash]["path"],
                            resource_entry["path"]
                        ]
                    })
                else:
                    hash_map[file_hash] = resource_entry
        
        project_entry["resource_count"] = len(project_entry["resources"])
        index["projects"][project_name] = project_entry
        index["total_projects"] += 1
        index["total_resources"] += project_entry["resource_count"]
    
    index["resources_by_modality"] = dict(index["resources_by_modality"])
    return index


def get_modality_from_ext(ext: str) -> str:
    """根据文件后缀判断模态"""
    image_exts = [".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tga"]
    video_exts = [".mp4", ".mov", ".avi", ".webm", ".mkv"]
    audio_exts = [".mp3", ".wav", ".ogg", ".m4a", ".flac"]
    text_exts = [".txt", ".md", ".json", ".xml", ".csv"]
    
    ext_lower = ext.lower()
    if ext_lower in image_exts:
        return "image"
    elif ext_lower in video_exts:
        return "video"
    elif ext_lower in audio_exts:
        return "audio"
    elif ext_lower in text_exts:
        return "text"
    return "unknown"


def infer_tags(filename: str, category: str, display_name: str = "", description: str = "") -> list:
    """根据文件名、显示名、描述、分类推断标签"""
    tags = [category]

    keywords = {
        "character": ["角色", "人物"],
        "scene": ["场景", "背景"],
        "skill": ["技能", "特效"],
        "ui": ["界面", "UI"],
        "item": ["道具", "物品"],
        "story": ["剧情", "故事"],
        "bgm": ["音乐", "BGM"],
        "sfx": ["音效", "声音"]
    }

    haystack = " ".join([filename, category, display_name, description]).lower()
    for kw, labels in keywords.items():
        if kw.lower() in haystack:
            tags.extend(labels)

    style_keywords = ["chinese", "fantasy", "scifi", "cartoon", "pixel", "anime", "realistic", "水墨", "古风", "仙侠", "rpg", "二次元"]
    for sk in style_keywords:
        if sk.lower() in haystack:
            tags.append(sk)

    return list(set(tags))


def save_index(index: dict):
    """保存索引到文件"""
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    print(f"✅ 索引已更新: {INDEX_PATH}")
    print(f"📊 统计:")
    print(f"   项目数: {index['total_projects']}")
    print(f"   资源总数: {index['total_resources']}")
    print(f"   图像: {index['resources_by_modality'].get('image', 0)}")
    print(f"   视频: {index['resources_by_modality'].get('video', 0)}")
    print(f"   音频: {index['resources_by_modality'].get('audio', 0)}")
    print(f"   音乐: {index['resources_by_modality'].get('music', 0)}")
    print(f"   文本: {index['resources_by_modality'].get('text', 0)}")
    if index["duplicates"]:
        print(f"   ⚠️ 发现重复资源: {len(index['duplicates'])} 组")


def search_resources(query: str = "", category: str = "", modality: str = "", tags: list = None):
    """搜索资源"""
    if not INDEX_PATH.exists():
        print("❌ 索引不存在，先运行: python index.py --rebuild")
        return []
    
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        index = json.load(f)
    
    results = []
    query_lower = query.lower()

    for res in index.get("global_catalog", []):
        match = True

        if query:
            searchable = " ".join([
                res.get("name", ""),
                res.get("display_name", ""),
                res.get("description", ""),
                res.get("resource_id", ""),
                res.get("project", ""),
            ]).lower()
            if query_lower not in searchable:
                match = False

        if category and res["category"] != category:
            match = False

        if modality and res["modality"] != modality:
            match = False

        if tags and not any(t in res.get("tags", []) for t in tags):
            match = False

        if match:
            results.append(res)

    return results


def reuse_resource(resource_id: str, target_project: str):
    """跨项目复用资源"""
    if not INDEX_PATH.exists():
        print("❌ 索引不存在")
        return False
    
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        index = json.load(f)
    
    # 查找资源
    source_res = None
    for res in index.get("global_catalog", []):
        if res["id"] == resource_id:
            source_res = res
            break
    
    if not source_res:
        print(f"❌ 资源不存在: {resource_id}")
        return False
    
    source_path = BASE_DIR / source_res["path"]
    target_dir = PROJECTS_DIR / target_project / source_res["category"]
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / source_res["filename"]
    
    shutil.copy2(source_path, target_path)
    print(f"✅ 已复用: {source_res['name']}")
    print(f"   从: {source_res['project']}")
    print(f"   到: {target_project}/{source_res['category']}/")
    return True


def list_projects():
    """列出所有项目"""
    if not INDEX_PATH.exists():
        print("❌ 索引不存在")
        return
    
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        index = json.load(f)
    
    print("📁 资源库项目列表:")
    print("-" * 60)
    for name, project in index.get("projects", {}).items():
        print(f"  🎮 {name}")
        print(f"     类型: {project['type']}")
        print(f"     资源: {project['resource_count']}")
        print(f"     路径: {project['path']}")
        print()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="游戏资源库索引管理")
    parser.add_argument("--rebuild", action="store_true", help="重建索引")
    parser.add_argument("--search", type=str, help="搜索关键词")
    parser.add_argument("--category", type=str, help="按分类筛选")
    parser.add_argument("--modality", type=str, help="按模态筛选 (image/video/audio/text)")
    parser.add_argument("--tags", type=str, nargs="+", help="按标签筛选")
    parser.add_argument("--list", action="store_true", help="列出所有项目")
    parser.add_argument("--reuse", type=str, help="复用资源ID")
    parser.add_argument("--to", type=str, help="目标项目（配合 --reuse）")
    
    args = parser.parse_args()
    
    if args.rebuild:
        index = scan_projects()
        save_index(index)
    
    elif args.search or args.category or args.modality or args.tags:
        results = search_resources(
            query=args.search or "",
            category=args.category or "",
            modality=args.modality or "",
            tags=args.tags
        )
        print(f"🔍 找到 {len(results)} 个资源:")
        print("-" * 60)
        for r in results[:50]:  # 最多显示50个
            name = r.get("display_name") or r["name"]
            print(f"  [{r['modality']}] {name}")
            print(f"     文件: {r['filename']}  |  ID: {r.get('resource_id', '-')}")
            print(f"     项目: {r['project']} | 分类: {r['category']}")
            print(f"     标签: {', '.join(r.get('tags', []))}")
            print(f"     路径: {r['path']}")
            if r.get("description"):
                print(f"     描述: {r['description']}")
            print()
    
    elif args.list:
        list_projects()
    
    elif args.reuse and args.to:
        reuse_resource(args.reuse, args.to)
    
    else:
        # 默认重建索引
        index = scan_projects()
        save_index(index)


if __name__ == "__main__":
    main()
