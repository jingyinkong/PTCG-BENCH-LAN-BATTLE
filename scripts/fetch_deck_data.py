#!/usr/bin/env python3
"""
从 tcg.mik.moe API 抓取 FGH-CSV9C 简中赛制下热门卡组数据。
用法: uv run python scripts/fetch_deck_data.py

流程:
1. deck-static-by-date-and-reg → 获取卡组类型列表 (前 11 个)
2. deck/core-card → 获取每个卡组类型的核心单卡
3. deck/category-recent-play → 获取最近比赛 (rank 降级策略)
4. deck/detail → 获取 60 张卡表
5. 输出 deck_data.json
"""
import asyncio
import json
import sys
import time
from pathlib import Path

import aiohttp

API_BASE = "https://tcg.mik.moe/api/v3"
OUTPUT_FILE = Path(__file__).parent.parent / "deck_data.json"

CONCURRENCY = 5
REGULATION = "FGH-CSV9C"
PAGE_SIZE = 30
TOP_N = 11


async def fetch_json(
    session: aiohttp.ClientSession,
    url: str,
    payload: dict,
    timeout: int = 30,
    max_retries: int = 3,
) -> dict:
    """POST JSON, return response dict. Retry on failure."""
    for attempt in range(max_retries):
        try:
            async with session.post(
                url, json=payload, timeout=aiohttp.ClientTimeout(total=timeout)
            ) as resp:
                data = await resp.json()
                if data.get("code") == 200:
                    return data
                print(f"  API error (attempt {attempt+1}): {data.get('msg', 'unknown')}")
        except Exception as e:
            print(f"  Request error (attempt {attempt+1}): {e}")
        if attempt < max_retries - 1:
            await asyncio.sleep(1 * (attempt + 1))
    return {"code": -1, "data": None}


async def fetch_deck_types(session: aiohttp.ClientSession) -> list[dict]:
    """Step 1: Get top deck types from deck-static-by-date-and-reg."""
    print("=== Step 1: Fetching deck types ===")
    data = await fetch_json(session, f"{API_BASE}/deck/deck-static-by-date-and-reg", {
        "regulationMark": REGULATION,
        "isVariant": True,
    })
    items = data.get("data", {}).get("list", [])
    top = items[:TOP_N]
    for i, d in enumerate(top):
        print(f"  {i+1}. [{d['id']}] {d['name']} ({d['label']}) share={d['share']:.2%}")
    return top


async def fetch_core_cards(session: aiohttp.ClientSession, deck: dict) -> dict:
    """Step 2: Get core cards for a deck type."""
    data = await fetch_json(session, f"{API_BASE}/deck/core-card", {
        "variant": deck["id"],
        "showPopular": True,
    })
    cards = data.get("data", {}).get("list", [])
    deck["core_cards"] = cards[:15]
    deck["core_card_count"] = len(cards)
    top_name = cards[0]["cardName"] if cards else "N/A"
    print(f"  [{deck['name']}] {len(cards)} core cards, top: {top_name}")
    return deck


async def fetch_recent_play(session: aiohttp.ClientSession, deck: dict) -> dict:
    """Step 3: Get recent tournament plays with rank degradation."""
    all_matches = []
    for page in [1, 2]:
        data = await fetch_json(session, f"{API_BASE}/deck/category-recent-play", {
            "id": deck["id"],
            "all": False,
            "page": page,
            "pageSize": PAGE_SIZE,
        })
        matches = data.get("data", {}).get("list", [])
        if not matches:
            break
        all_matches.extend(matches)

    if not all_matches:
        print(f"  [{deck['name']}] No recent plays found!")
        deck["best_match"] = None
        return deck

    all_matches.sort(key=lambda m: (m.get("rank", 999), m.get("date", "")), reverse=False)
    best = all_matches[0]
    deck["best_match"] = {
        "tournamentId": best["tournamentId"],
        "tournamentName": best["tournamentName"],
        "playerName": best["playerName"],
        "rank": best["rank"],
        "points": best["points"],
        "deckId": best["deckId"],
        "date": best["date"],
    }
    print(f"  [{deck['name']}] best: rank={best['rank']} deckId={best['deckId']}")
    return deck


async def fetch_deck_detail(session: aiohttp.ClientSession, deck: dict) -> dict:
    """Step 4: Get full 60-card deck list from deck/detail."""
    best = deck.get("best_match")
    if not best:
        deck["full_deck"] = None
        return deck

    data = await fetch_json(session, f"{API_BASE}/deck/detail", {"deckId": best["deckId"]})
    cards = data.get("data", {}).get("cards", [])

    deck["full_deck"] = []
    for c in cards:
        deck["full_deck"].append({
            "count": c.get("count", 1),
            "cardName": c.get("cardName", ""),
            "setCode": c.get("setCode", ""),
            "cardIndex": c.get("cardIndex", ""),
            "setCodeEn": c.get("setCodeEn", ""),
            "cardIndexEn": c.get("cardIndexEn", ""),
            "nameEn": c.get("nameEn", ""),
            "cardType": c.get("cardType", ""),
        })

    total = sum(c["count"] for c in deck["full_deck"])
    print(f"  [{deck['name']}] {len(deck['full_deck'])} unique, {total} total cards")
    return deck


async def main():
    print("PTCG Deck Data Fetcher - FGH-CSV9C")
    print("=" * 50)

    connector = aiohttp.TCPConnector(limit=CONCURRENCY)
    async with aiohttp.ClientSession(connector=connector) as session:
        deck_types = await fetch_deck_types(session)
        if not deck_types:
            print("ERROR: No deck types returned!")
            sys.exit(1)

        print(f"\n=== Step 2: Fetching core cards ===")
        deck_types = await asyncio.gather(*[
            fetch_core_cards(session, d) for d in deck_types
        ])

        print(f"\n=== Step 3: Fetching recent plays ===")
        deck_types = await asyncio.gather(*[
            fetch_recent_play(session, d) for d in deck_types
        ])

        print(f"\n=== Step 4: Fetching deck details ===")
        deck_types = await asyncio.gather(*[
            fetch_deck_detail(session, d) for d in deck_types
        ])

    output = {
        "regulation": REGULATION,
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        "total_decks": len(deck_types),
        "decks": deck_types,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\nOutput written to {OUTPUT_FILE}")

    for d in deck_types:
        has = "Y" if d.get("full_deck") else "N"
        total = sum(c["count"] for c in d.get("full_deck", []))
        print(f"  [{has}] {d['name']}: {d.get('core_card_count', 0)} core, {total} cards in deck")


if __name__ == "__main__":
    asyncio.run(main())
