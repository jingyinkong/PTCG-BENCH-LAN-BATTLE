#!/usr/bin/env python3
"""从 deck_data.json 生成 ptcg/decks/ 下的卡组文件并更新 deck_manager.py。"""
import json
import sys
from pathlib import Path

DECK_DATA = Path(__file__).parent.parent / "deck_data.json"
DECKS_DIR = Path(__file__).parent.parent / "ptcg" / "decks"
DECK_MANAGER = Path(__file__).parent.parent / "backend" / "deck_manager.py"

# CN deck name → English slug
SLUG_MAP = {
    "喷火龙 大比鸟": "charizard_ex",
    "雷吉铎拉戈": "regidrago_vstar",
    "密勒顿": "miraidon_ex",
    "沙奈朵": "gardevori_ex",
    "猛雷鼓 厄诡椪": "raging_bolt_ogerpon_ex",
    "起源帕路奇亚 猫头夜鹰": "origin_palkia_noctowl_vstar",
    "毛崖蟹 太乐巴戈斯": "klawf_terapagos",
    "铝钢桥龙 帝牙卢卡": "archaludon_dialga_ex",
    "赛富豪": "gholdengo_ex",
    "洛奇亚 始祖大鸟": "lugia_archeops",
    "太乐巴戈斯 猫头夜鹰": "terapagos_noctowl_ex",
}

# Card type → deck file section
CAT_HEADER = {
    "Pokemon": "Pokémon", "Pokémon": "Pokémon",
    "Item": "Trainer", "Supporter": "Trainer",
    "Stadium": "Trainer", "Tool": "Trainer",
    "Pokémon Tool": "Trainer",
    "Basic Energy": "Energy", "Special Energy": "Energy",
}


def write_deck_file(deck):
    slug = SLUG_MAP.get(deck["name"])
    if not slug:
        print(f"  SKIP: no slug for '{deck['name']}'")
        return None
    cards = deck.get("full_deck", [])
    if not cards:
        print(f"  SKIP: no cards for '{deck['name']}'")
        return None

    groups = {"Pokémon": [], "Trainer": [], "Energy": []}
    for c in cards:
        cat = CAT_HEADER.get(c.get("cardType", ""), "Trainer")
        groups.setdefault(cat, []).append(c)

    lines = []
    for cat_name in ["Pokémon", "Trainer", "Energy"]:
        items = groups.get(cat_name, [])
        if not items:
            continue
        total = sum(c["count"] for c in items)
        lines.append(f"{cat_name}: {total}")
        for c in items:
            lines.append(f"{c['count']} {c['nameEn']} {c['setCodeEn']} {c['cardIndexEn']}")
        lines.append("")

    fpath = DECKS_DIR / f"{slug}.txt"
    fpath.write_text("\n".join(lines), encoding="utf-8")
    t = sum(c["count"] for c in cards)
    print(f"  OK {fpath.name}: {t} cards")
    return slug


def update_deck_manager(slugs):
    content = DECK_MANAGER.read_text()
    names_str = "[" + ", ".join(f'"{s}"' for s in sorted(slugs)) + "]"
    new_lines = []
    found = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("_BUILTIN_DECK_NAMES") and not found:
            new_lines.append(f"_BUILTIN_DECK_NAMES = {names_str}")
            found = True
        else:
            new_lines.append(line)
    if found:
        DECK_MANAGER.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        print(f"  Updated deck_manager: {names_str}")
    else:
        print("  ERROR: _BUILTIN_DECK_NAMES not found!")


def main():
    with open(DECK_DATA) as f:
        data = json.load(f)
    print(f"Generating {len(data['decks'])} deck files...")
    slugs = []
    for deck in data["decks"]:
        s = write_deck_file(deck)
        if s:
            slugs.append(s)
    print(f"\nUpdating deck_manager.py...")
    update_deck_manager(slugs)
    print(f"\nDone: {len(slugs)} decks written.")


if __name__ == "__main__":
    main()
