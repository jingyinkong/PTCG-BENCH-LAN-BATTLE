#!/usr/bin/env python3
"""
异步并发下载中文卡图并更新 card_data_cache.json。
用法: uv run python scripts/download_card_images.py [-c 15] [--dry-run]
"""
import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

import aiohttp

IMAGES_DIR = Path(__file__).parent.parent / "frontend" / "public" / "cards"
DATA_FILE = Path(__file__).parent.parent / "card_chinese_data.json"
CACHE_FILE = Path(__file__).parent.parent / "card_data_cache.json"

DEFAULT_CONCURRENCY = 15
REQUEST_TIMEOUT = 20
_start_time: float = 0


async def download_one(session: aiohttp.ClientSession, card: tuple,
                       sem: asyncio.Semaphore, timeout: int) -> tuple[str, bool, int]:
    """异步下载单张卡图。返回 (filename, success, bytes)。"""
    en_name, info = card
    url = info.get("image_url", "")
    set_cn = info.get("set_code_cn", "")
    idx_cn = info.get("card_index_cn", "")

    if not url:
        return ("", True, 0)

    filename = f"{set_cn}-{idx_cn}.png"
    dest = IMAGES_DIR / filename

    if dest.exists() and dest.stat().st_size > 0:
        return (filename, True, dest.stat().st_size)

    async with sem:
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(data)
                    return (filename, True, len(data))
        except Exception:
            pass
    return (filename, False, 0)


async def run(cards: dict, concurrency: int, timeout: int) -> tuple[int, int, int]:
    """异步下载所有卡图。"""
    sem = asyncio.Semaphore(concurrency)
    connector = aiohttp.TCPConnector(limit=concurrency + 10, limit_per_host=concurrency + 5)

    # 过滤已存在的
    items = []
    skipped = 0
    for en_name, info in cards.items():
        set_cn = info.get("set_code_cn", "")
        idx_cn = info.get("card_index_cn", "")
        dest = IMAGES_DIR / f"{set_cn}-{idx_cn}.png"
        if dest.exists():
            skipped += 1
        else:
            items.append((en_name, info))

    if not items:
        return 0, skipped, 0

    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [download_one(session, item, sem, timeout) for item in items]
        downloaded = 0
        failed = 0
        total_bytes = 0

        for i, coro in enumerate(asyncio.as_completed(tasks)):
            filename, ok, size = await coro
            if ok:
                downloaded += 1
                total_bytes += size
            else:
                failed += 1
            pct = (i + 1) * 100 // len(tasks)
            mb = total_bytes / (1024 * 1024)
            elapsed = time.time() - _start_time
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            eta = (len(tasks) - i - 1) / rate if rate > 0 else 0
            sys.stderr.write(f"\r  [{pct:3d}%] {i+1}/{len(tasks)} | {elapsed:.0f}s | {mb:.1f}MB | ~{eta:.0f}s  ")

        sys.stderr.write("\n")
    return downloaded, skipped, failed


def main():
    parser = argparse.ArgumentParser(description="异步并发下载中文卡图")
    parser.add_argument("-c", "--concurrency", type=int, default=DEFAULT_CONCURRENCY)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    global _start_time
    _start_time = time.time()

    if not DATA_FILE.exists():
        print(f"[ERROR] {DATA_FILE} 不存在")
        sys.exit(1)

    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    cards = data.get("cards", {})

    print("=" * 60)
    print("PTCG 中文卡图下载（asyncio 异步并发）")
    print(f"并发: {args.concurrency} | 卡片: {len(cards)} 张")
    if args.dry_run:
        print("DRY-RUN")
    print("=" * 60)

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        missing = sum(1 for info in cards.values()
                      if not (IMAGES_DIR / f"{info.get('set_code_cn','')}-{info.get('card_index_cn','')}.png").exists())
        print(f"需下载: {missing}/{len(cards)} 张")
        return 0

    downloaded, skipped, failed = asyncio.run(run(cards, args.concurrency, REQUEST_TIMEOUT))

    elapsed = time.time() - _start_time
    total = len(cards)
    print(f"下载: {downloaded} | 已存在: {skipped} | 失败: {failed} | {elapsed:.0f}s")

    # 更新 cache 为本地路径
    print(f"\n更新 {CACHE_FILE}...")
    cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    updated = 0
    # card_data_cache.json key 格式: "{set_name}-{number}" (如 "SVI-086")
    # card_chinese_data.json 有 set_name 和 number 字段
    for name_key, cd in cards.items():
        set_name = cd.get("set_name", "")
        number = cd.get("number", "")
        if set_name and number:
            # 尝试带前导零和不带前导零两种格式
            num_raw = str(number)
            num_normalized = str(int(num_raw)) if num_raw.isdigit() else num_raw
            for candidate in [f"{set_name}-{num_raw}", f"{set_name}-{num_normalized}"]:
                if candidate in cache:
                    entry = cache[candidate]
                    entry["name"] = cd.get("chinese_name", entry.get("name", ""))
                    entry["img"] = f"/cards/{cd['set_code_cn']}-{cd['card_index_cn']}.png"
                    updated += 1
                    break
    CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已更新 {updated} 条为本地路径 /cards/")
    print("完成!")


if __name__ == "__main__":
    main()
