#!/usr/bin/env python3
"""
异步并发从 tcg.mik.moe API 抓取卡片中文数据。
用法: uv run python scripts/fetch_chinese_card_data.py [-c 20]
"""
import argparse
import asyncio
import ast
import json
import sys
import time
from pathlib import Path

import aiohttp

TCG_API_SEARCH = "https://tcg.mik.moe/api/v3/card/card-basic-search"
IMAGE_BASE = "https://tcg.mik.moe/static/img"
CARDS_DIR = Path(__file__).parent.parent / "ptcg" / "cards"
OUTPUT_FILE = Path(__file__).parent.parent / "card_chinese_data.json"
DATA_DIR = Path(__file__).parent.parent / "card_data"

DEFAULT_CONCURRENCY = 20
DEFAULT_TIMEOUT = 10


def extract_card_info(file_path: Path) -> dict | None:
    """从 Python 卡片文件中提取英文名称。"""
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
    except SyntaxError:
        return None

    set_name = file_path.parent.name
    card_name = None
    attacks = []
    abilities = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if (isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name)
                    and target.value.id == "self" and target.attr == "name"
                    and isinstance(node.value, ast.Constant)):
                    if card_name is None:
                        card_name = node.value.value

        if isinstance(node, ast.Call):
            fn = getattr(node.func, "id", "")
            if fn == "Attack":
                for kw in getattr(node, "keywords", []):
                    if kw.arg == "name" and isinstance(kw.value, ast.Constant):
                        attacks.append(kw.value.value)
            if "Ability" in fn:
                for kw in getattr(node, "keywords", []):
                    if kw.arg == "name" and isinstance(kw.value, ast.Constant):
                        abilities.append(kw.value.value)

    return {
        "english_name": card_name,
        "set_code_en": set_name,
        "file": str(file_path.relative_to(CARDS_DIR.parent)),
        "attacks_en": attacks,
        "abilities_en": abilities,
    } if card_name else None


async def fetch_one(session: aiohttp.ClientSession, card: dict,
                    timeout: int, sem: asyncio.Semaphore) -> dict | None:
    """异步获取单张卡片的中文数据（仅搜索，跳过详情提速）。"""
    en_name = card["english_name"]
    set_en = card["set_code_en"]
    safe_name = en_name.replace("/", "_").replace("'", "").replace(" ", "_")

    # 检查缓存
    card_file = DATA_DIR / f"{safe_name}.json"
    if card_file.exists():
        try:
            cached = json.loads(card_file.read_text(encoding="utf-8"))
            if cached.get("status") == "ok":
                return cached["data"]
        except Exception:
            pass

    async with sem:  # 控制并发
        try:
            async with session.post(
                TCG_API_SEARCH,
                json={"SearchText": en_name, "PageSize": 10, "Page": 1},
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as resp:
                if resp.status != 200:
                    _save_cache(card_file, "error", None)
                    return None
                data = await resp.json()
                if data.get("code") != 200 or not data["data"].get("list"):
                    _save_cache(card_file, "not_found", None)
                    return None

            results = data["data"]["list"]

            # 匹配最佳结果
            matched = None
            for r in results:
                if r.get("setCodeEn", "").upper() == set_en.upper():
                    matched = r
                    break
            if matched is None:
                matched = results[0]

            set_code_cn = matched.get("setCode", "")
            card_index_cn = matched.get("cardIndex", "")
            cn_name = matched.get("cardName", "")

            result = {
                "english_name": en_name,
                "set_code_en": set_en,
                "chinese_name": cn_name,
                "set_code_cn": set_code_cn,
                "card_index_cn": card_index_cn,
                "image_url": f"{IMAGE_BASE}/{set_code_cn}/{card_index_cn}.png",
                "attacks_en": card["attacks_en"],
                "attacks_cn": [],
                "abilities_en": card["abilities_en"],
                "abilities_cn": [],
                "file": card["file"],
            }
            _save_cache(card_file, "ok", result)
            return result

        except asyncio.TimeoutError:
            _save_cache(card_file, "error", None)
            return None
        except Exception:
            _save_cache(card_file, "error", None)
            return None


def _save_cache(path: Path, status: str, data: dict | None):
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {"status": status, "data": data}
    path.write_text(json.dumps(entry, ensure_ascii=False), encoding="utf-8")


async def run(cards: list, concurrency: int, timeout: int):
    """主异步函数。"""
    sem = asyncio.Semaphore(concurrency)
    connector = aiohttp.TCPConnector(limit=concurrency + 10, limit_per_host=concurrency + 5)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [fetch_one(session, card, timeout, sem) for card in cards]
        results = []
        for i, coro in enumerate(asyncio.as_completed(tasks)):
            result = await coro
            pct = (i + 1) * 100 // len(tasks)
            bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
            elapsed = time.time() - _start_time
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            eta = (len(tasks) - i - 1) / rate if rate > 0 else 0
            label = result["chinese_name"] if result else "未找到"
            sys.stderr.write(f"\r  [{bar}] {pct:3d}% ({i+1}/{len(tasks)}) "
                             f"| {elapsed:.0f}s | {rate:.1f}张/s | 剩余~{eta:.0f}s | {label}")
            results.append(result)
        sys.stderr.write("\n")
    return results


_start_time: float = 0


def main():
    parser = argparse.ArgumentParser(description="异步并发抓取卡片中文数据")
    parser.add_argument("-c", "--concurrency", type=int, default=DEFAULT_CONCURRENCY,
                        help=f"并发数（默认 {DEFAULT_CONCURRENCY}）")
    parser.add_argument("-t", "--timeout", type=int, default=DEFAULT_TIMEOUT,
                        help=f"请求超时秒数（默认 {DEFAULT_TIMEOUT}s）")
    parser.add_argument("--no-cache", action="store_true", help="重新抓取，忽略缓存")
    args = parser.parse_args()

    global _start_time
    _start_time = time.time()

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("PTCG 卡片中文数据抓取（asyncio 异步并发）")
    print(f"并发: {args.concurrency} | 超时: {args.timeout}s | 缓存: {DATA_DIR}")
    print("=" * 60)

    # Step 1: 扫描
    print("\n[Step 1] 扫描卡片文件...")
    all_cards = []
    for pf in sorted(CARDS_DIR.rglob("*.py")):
        if pf.name.startswith("__"):
            continue
        info = extract_card_info(pf)
        if info:
            all_cards.append(info)

    if args.no_cache:
        for f in DATA_DIR.glob("*.json"):
            f.unlink()
        cards = all_cards
        cached = 0
    else:
        cards = []
        for c in all_cards:
            safe = c["english_name"].replace("/", "_").replace("'", "").replace(" ", "_")
            cf = DATA_DIR / f"{safe}.json"
            if cf.exists():
                try:
                    cached_data = json.loads(cf.read_text(encoding="utf-8"))
                    if cached_data.get("status") == "ok":
                        continue
                except Exception:
                    pass
            cards.append(c)
        cached = len(all_cards) - len(cards)

    print(f"共 {len(all_cards)} 张（缓存 {cached} 张，需抓取 {len(cards)} 张）")

    if not cards:
        print("所有卡片已缓存。")
    else:
        print(f"\n[Step 2] 异步并发抓取（{args.concurrency} 并发）...")
        results = asyncio.run(run(cards, args.concurrency, args.timeout))
        elapsed = time.time() - _start_time
        matched = sum(1 for r in results if r is not None)
        print(f"  完成! {elapsed:.0f}s | 匹配 {matched}/{len(cards)} 张")

    # Step 3: 合并
    print(f"\n[Step 3] 合并缓存 → {OUTPUT_FILE}")
    merged = {}
    not_found = []
    errors = 0

    for f in sorted(DATA_DIR.glob("*.json")):
        try:
            entry = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            errors += 1
            continue
        if entry.get("status") == "ok" and entry.get("data"):
            merged[entry["data"]["english_name"]] = entry["data"]
        elif entry.get("status") == "not_found":
            not_found.append(f.stem.replace("_", " "))
        else:
            errors += 1

    elapsed = time.time() - _start_time
    output = {
        "metadata": {
            "source": "https://tcg.mik.moe/",
            "total": len(all_cards),
            "matched": len(merged),
            "not_found": len(not_found),
            "errors": errors,
            "elapsed_seconds": round(elapsed, 1),
            "concurrency": args.concurrency,
        },
        "cards": merged,
        "not_found": not_found,
    }
    OUTPUT_FILE.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"匹配: {len(merged)} | 未找到: {len(not_found)} | 错误: {errors} | {elapsed:.0f}s")

    if not_found:
        print(f"\n⚠ 未找到 ({len(not_found)}):")
        for name in sorted(not_found)[:10]:
            print(f"  - {name}")

    print("完成!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
