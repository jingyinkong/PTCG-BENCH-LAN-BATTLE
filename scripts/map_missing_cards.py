#!/usr/bin/env python3
"""查询 tcg.mik.moe API 获取缺失核心卡牌的英文 setCode 映射。
用法: uv run python scripts/map_missing_cards.py
"""
import asyncio, json, sys
from pathlib import Path
import aiohttp

API_SEARCH = "https://tcg.mik.moe/api/v3/card/card-basic-search"
API_DETAIL = "https://tcg.mik.moe/api/v3/card/card-detail"
DECK_DATA = Path(__file__).parent.parent / "deck_data.json"
CACHE_PATH = Path(__file__).parent.parent / "card_data_cache.json"
CONC = 5


async def search(session, name):
    try:
        async with session.post(API_SEARCH,
            json={"searchText": name, "page": 1, "pageSize": 3},
            timeout=aiohttp.ClientTimeout(total=10)) as r:
            d = await r.json()
            return d["data"]["list"] if d.get("code") == 200 else []
    except Exception:
        return []


async def detail(session, sc, ci):
    try:
        async with session.post(API_DETAIL,
            json={"setCode": sc, "cardIndex": str(ci)},
            timeout=aiohttp.ClientTimeout(total=10)) as r:
            d = await r.json()
            return d["data"] if d.get("code") == 200 else None
    except Exception:
        return None


async def main():
    with open(DECK_DATA) as f:
        ddata = json.load(f)
    with open(CACHE_PATH) as f:
        cache = json.load(f)

    cache_names = {v.get("name", ""): k for k, v in cache.items()}

    missing = {}
    for deck in ddata["decks"]:
        for c in deck.get("core_cards", []):
            name = c["cardName"]
            if c["cardType"] == "Basic Energy" or name in cache_names or name in missing:
                continue
            missing[name] = {"sc": c["setCode"], "ci": c["cardIndex"], "type": c["cardType"]}

    print(f"缺失卡牌: {len(missing)}\n")

    connector = aiohttp.TCPConnector(limit=CONC)
    async with aiohttp.ClientSession(connector=connector) as session:
        for name, info in sorted(missing.items()):
            results = await search(session, name)
            if not results:
                print(f"  NO_RESULT: {name}")
                continue

            best = results[0]
            for r in results:
                if str(r.get("cardIndex", "")) == info["ci"]:
                    best = r
                    break

            d = await detail(session, best["setCode"], best["cardIndex"])
            if d:
                en_set = d.get("setCodeEn", "?")
                en_idx = str(d.get("cardIndexEn", "?")).zfill(3)
                print(f"  {name}: {en_set}-{en_idx} ({d.get('nameEn','?')}) [{d.get('cardType','?')}]")
            else:
                print(f"  NO_DETAIL: {name} ({best['setCode']}-{best['cardIndex']})")

            await asyncio.sleep(0.3)


if __name__ == "__main__":
    asyncio.run(main())
