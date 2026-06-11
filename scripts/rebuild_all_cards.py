#!/usr/bin/env python3
"""全量重建所有卡牌——从 tcg.mik.moe API 使用中文 setCode 抓取中文文本。
用法: uv run python scripts/rebuild_all_cards.py [--force]
"""
import asyncio, json, sys, re
from pathlib import Path
import aiohttp

API = "https://tcg.mik.moe/api/v3"
DECK_DATA = Path(__file__).parent.parent / "deck_data.json"
CACHE = Path(__file__).parent.parent / "card_data_cache.json"
CARDS_DIR = Path(__file__).parent.parent / "ptcg" / "cards"
CONC = 5

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.gen_cards import generate, cls_name, safe_str


async def fetch_detail(session, set_code, card_index):
    """用中文setCode查API."""
    for attempt in range(3):
        try:
            async with session.post(f"{API}/card/card-detail",
                json={"setCode": set_code, "cardIndex": str(card_index)},
                timeout=aiohttp.ClientTimeout(total=15)) as r:
                d = await r.json()
                if d.get("code") == 200:
                    return d["data"]
        except Exception:
            await asyncio.sleep(0.5)
    return None


async def main():
    force = "--force" in sys.argv
    
    with open(DECK_DATA) as f:
        ddata = json.load(f)
    
    # 建立 core_cards 的中文setCode映射
    chinese_map = {}  # (setCodeEn, cardIndexEn) → (chineseSetCode, chineseCardIndex)
    name_map = {}     # cardName → (chineseSetCode, chineseCardIndex)
    
    for deck in ddata["decks"]:
        for c in deck.get("core_cards", []):
            name = c["cardName"]
            if c["cardType"] == "Basic Energy":
                continue
            key = (c.get("setCodeEn",""), c.get("cardIndexEn",""))
            val = (c["setCode"], c["cardIndex"])
            if key not in chinese_map:
                chinese_map[key] = val
            if name not in name_map:
                name_map[name] = val
    
    # 也加入 full_deck
    for deck in ddata["decks"]:
        for c in deck.get("full_deck", []):
            key = (c.get("setCodeEn",""), c.get("cardIndexEn",""))
            val = (c.get("setCode"), c.get("cardIndex"))
            if key not in chinese_map:
                chinese_map[key] = val
            name = c["cardName"]
            if name not in name_map:
                name_map[name] = val
    
    print(f"中文setCode映射: {len(chinese_map)} (en) + {len(name_map)} (name)")
    
    # 获取所有已注册卡牌
    from ptcg.core.card_registry import registry
    registry._ensure_loaded()
    
    all_ids = sorted(registry.list_all())
    print(f"已注册卡牌: {len(all_ids)}")
    
    # 为每张卡找到中文setCode
    to_rebuild = []
    for cid in all_ids:
        exp, num = cid.split("-")
        num_z = str(int(num)).zfill(3)
        key = (exp, num_z)
        
        if key in chinese_map:
            ch_sc, ch_ci = chinese_map[key]
            to_rebuild.append((cid, ch_sc, ch_ci, exp, num_z))
        else:
            cls = registry.get(cid)
            if cls:
                inst = cls()
                name = getattr(inst, 'card_name', '?') or getattr(inst, 'name', '?')
                if name in name_map:
                    ch_sc, ch_ci = name_map[name]
                    to_rebuild.append((cid, ch_sc, ch_ci, exp, num_z))
                else:
                    to_rebuild.append((cid, exp, int(num), exp, num_z))
                    print(f"  FALLBACK: {cid} {name}")
    
    print(f"可重建: {len(to_rebuild)}")
    
    if not force:
        print("\n加 --force 执行重建")
        return
    
    # 全量重建
    connector = aiohttp.TCPConnector(limit=CONC)
    async with aiohttp.ClientSession(connector=connector) as session:
        rebuilt = 0
        failed = 0
        
        for cid, ch_sc, ch_ci, en_exp, en_num in to_rebuild:
            data = await fetch_detail(session, ch_sc, ch_ci)
            if not data:
                print(f"  FAIL: {cid} ({ch_sc}-{ch_ci})")
                failed += 1
                continue
            
            info = {"setCodeEn": data.get("setCodeEn", en_exp),
                    "cardIndexEn": data.get("cardIndexEn", en_num)}
            code = generate(data, info)
            
            sdir = CARDS_DIR / info["setCodeEn"]
            sdir.mkdir(exist_ok=True)
            (sdir / "__init__.py").touch()
            
            en_name = data.get("nameEn", "")
            fname = cls_name(safe_str(en_name), info["setCodeEn"],
                           str(info["cardIndexEn"]).zfill(3)).lower() + ".py"
            fpath = sdir / fname
            
            # 删除旧文件（如果改名了）
            old_pattern = f"{en_exp}{num_z}" if en_exp == info["setCodeEn"] else None
            
            fpath.write_text(code, encoding="utf-8")
            
            # 检查中文文本
            has_cn = bool(re.search(r'[一-鿿]{5,}', code))
            rebuilt += 1
            cn_name = data.get("name", "?")
            status = "CN" if has_cn else "EN!"
            print(f"  [{status}] {cid} → {info['setCodeEn']}-{info['cardIndexEn']} {cn_name}")
            
            await asyncio.sleep(0.2)
    
    print(f"\n重建: {rebuilt} 成功, {failed} 失败")
    
    # 重新加载 registry
    registry._loaded = False
    registry._ensure_loaded()
    print(f"Registry: {len(registry.list_all())} 张卡")


if __name__ == "__main__":
    asyncio.run(main())
