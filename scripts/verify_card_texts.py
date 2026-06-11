#!/usr/bin/env python3
"""全量核对所有卡牌文本与 tcg.mik.moe API 的一致性。
用法: uv run python scripts/verify_card_texts.py
"""
import asyncio, json, sys, re
from pathlib import Path
import aiohttp

API = "https://tcg.mik.moe/api/v3"
DECK_DATA = Path(__file__).parent.parent / "deck_data.json"
CONC = 3

sys.path.insert(0, str(Path(__file__).parent.parent))
from ptcg.core.card_registry import registry
from ptcg.core.card import PokemonCard, TrainerCard, EnergyCard
registry._ensure_loaded()


def normalize(s):
    return re.sub(r'\s+', '', str(s or '')).strip()


async def search_card(session, name):
    try:
        async with session.post(f"{API}/card/card-basic-search",
            json={"searchText": name, "page": 1, "pageSize": 3},
            timeout=aiohttp.ClientTimeout(total=10)) as r:
            d = await r.json()
            return d["data"]["list"] if d.get("code") == 200 else []
    except: return []


async def fetch_detail(session, sc, ci):
    try:
        async with session.post(f"{API}/card/card-detail",
            json={"setCode": sc, "cardIndex": str(ci)},
            timeout=aiohttp.ClientTimeout(total=10)) as r:
            d = await r.json()
            return d["data"] if d.get("code") == 200 else None
    except: return None


async def main():
    # Build Chinese setCode mapping
    with open(DECK_DATA) as f:
        ddata = json.load(f)
    ch_map = {}
    for deck in ddata["decks"]:
        for c in deck.get("core_cards", []):
            k = (c.get("setCodeEn",""), str(c.get("cardIndexEn","")))
            if k not in ch_map:
                ch_map[k] = (c["setCode"], c["cardIndex"])
        for c in deck.get("full_deck", []):
            k = (c.get("setCodeEn",""), str(c.get("cardIndexEn","")))
            if k not in ch_map:
                ch_map[k] = (c.get("setCode"), c.get("cardIndex"))
    
    all_ids = sorted(registry.list_all())
    results = {"match": 0, "mismatch": [], "no_api": [], "no_map": []}
    
    connector = aiohttp.TCPConnector(limit=CONC)
    async with aiohttp.ClientSession(connector=connector) as session:
        for cid in all_ids:
            exp, num = cid.split("-")
            num_z = str(int(num)).zfill(3)
            
            # Get Chinese setCode
            ch_sc, ch_ci = None, None
            key = (exp, num_z)
            if key in ch_map:
                ch_sc, ch_ci = ch_map[key]
            
            if not ch_sc:
                # Try search by card name
                cls = registry.get(cid)
                if not cls: continue
                inst = cls()
                name = getattr(inst, 'card_name', '?') or getattr(inst, 'name', '?')
                if not name or name == '?': continue
                search_results = await search_card(session, name)
                if search_results:
                    ch_sc = search_results[0]["setCode"]
                    ch_ci = search_results[0]["cardIndex"]
                else:
                    results["no_map"].append(cid)
                    continue
                await asyncio.sleep(0.3)
            
            # Fetch API data
            api_data = await fetch_detail(session, ch_sc, ch_ci)
            if not api_data:
                results["no_api"].append(cid)
                continue
            
            # Compare with code
            cls = registry.get(cid)
            inst = cls()
            
            mismatches = []
            
            if isinstance(inst, TrainerCard) or isinstance(inst, EnergyCard):
                code_t = normalize(getattr(inst, 'text', '') or '')
                api_t = normalize(api_data.get("description", "") or "")
                if code_t and api_t and code_t != api_t:
                    mismatches.append(("card_text", code_t[:80], api_t[:80]))
            
            elif isinstance(inst, PokemonCard):
                pa = api_data.get("pokemonAttr", {})
                api_atks = pa.get("attack", [])
                api_abs = pa.get("ability", [])
                code_atks = getattr(inst, 'attacks', []) or []
                code_abs = getattr(inst, 'ability', []) or []
                
                for i, (ca, cd) in enumerate(zip(api_atks, code_atks)):
                    api_t = normalize(ca.get("text", ""))
                    code_t = normalize(getattr(cd, 'text', '') or '')
                    if api_t and code_t and api_t != code_t:
                        mismatches.append((f"attack_{i}", code_t[:80], api_t[:80]))
                
                for i, (aa, ad) in enumerate(zip(api_abs, code_abs)):
                    api_t = normalize(aa.get("text", ""))
                    code_t = normalize(getattr(ad, 'text', '') or '')
                    if api_t and code_t and api_t != code_t:
                        mismatches.append((f"ability_{i}", code_t[:80], api_t[:80]))
            
            if mismatches:
                results["mismatch"].append((cid, mismatches))
            else:
                results["match"] += 1
            
            await asyncio.sleep(0.15)
    
    print(f"核对完成: {len(all_ids)} 张卡")
    print(f"  一致: {results['match']}")
    print(f"  不一致: {len(results['mismatch'])}")
    print(f"  API无数据: {len(results['no_api'])}")
    print(f"  无映射: {len(results['no_map'])}")
    
    if results["mismatch"]:
        print("\n=== 文本不一致 ===")
        for cid, mismatches in results["mismatch"]:
            print(f"\n{cid}:")
            for field, code_t, api_t in mismatches:
                print(f"  {field}:")
                print(f"    代码: {code_t}")
                print(f"    API:  {api_t}")
    
    if results["no_api"]:
        print(f"\n=== API无数据 ({len(results['no_api'])}) ===")
        for cid in results["no_api"][:20]:
            print(f"  {cid}")
    
    if results["no_map"]:
        print(f"\n=== 无中文setCode映射 ({len(results['no_map'])}) ===")
        for cid in results["no_map"][:20]:
            print(f"  {cid}")


if __name__ == "__main__":
    asyncio.run(main())
