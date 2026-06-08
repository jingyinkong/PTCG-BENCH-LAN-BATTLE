#!/usr/bin/env python3
"""
为 deck_data.json 中所有缺失的卡牌查询 card-detail API 获取详细信息，
生成正确的 Python 卡片类（带 get_actions/reduce_action）。

用法: uv run python scripts/bootstrap_missing_cards.py [--dry-run]
"""
import asyncio
import json
import sys
import re
import time
from pathlib import Path

import aiohttp

API_BASE = "https://tcg.mik.moe/api/v3"
DECK_DATA = Path(__file__).parent.parent / "deck_data.json"
CARDS_DIR = Path(__file__).parent.parent / "ptcg" / "cards"

CONCURRENCY = 10


async def fetch_card_detail(
    session: aiohttp.ClientSession,
    set_code: str,  # CN format like "CS5aC"
    card_index: str,  # CN format like "099"
    retries: int = 3,
) -> dict | None:
    for attempt in range(retries):
        try:
            async with session.post(
                f"{API_BASE}/card/card-detail",
                json={"setCode": set_code, "cardIndex": card_index},
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                data = await resp.json()
                if data.get("code") == 200:
                    return data.get("data")
        except Exception:
            if attempt < retries - 1:
                await asyncio.sleep(0.5 * (attempt + 1))
    return None


def get_missing_cards() -> list[dict]:
    with open(DECK_DATA) as f:
        data = json.load(f)

    all_cards = {}
    for deck in data["decks"]:
        for c in deck.get("full_deck", []):
            key = (c["setCodeEn"], c["cardIndexEn"])
            if key not in all_cards:
                all_cards[key] = c

    from ptcg.core.card_registry import registry
    existing_ids = set(registry.list_all())

    missing = []
    for (sc, idx), c in sorted(all_cards.items()):
        card_id = f"{sc}-{idx}"
        if card_id not in existing_ids:
            c["_card_id"] = card_id
            missing.append(c)
    return missing


def _make_class_name(name_en: str, set_code: str, number: str) -> str:
    """Generate class name like 'SVE002BasicFireEnergy' or 'PAR088Gimmighoul'."""
    clean = name_en.replace(" ", "").replace("-", "").replace("'", "").replace(".", "")
    clean = clean.replace("é", "e").replace("è", "e").replace("ê", "e")
    clean = re.sub(r'[^a-zA-Z0-9]', '', clean)
    return f"{set_code}{number}{clean}"


def _is_pokemon(api_data: dict) -> bool:
    """Determine if this is a Pokemon card from API data."""
    ct = api_data.get("cardType", "")
    return ct in ("Pokemon", "Pokémon")


def _card_type_from_api(api_data: dict) -> str:
    """Map API energy type to CardType enum value."""
    if not _is_pokemon(api_data):
        return None
    pa = api_data.get("pokemonAttr", {})
    et = pa.get("energyType", "C")
    mapping = {
        "C": "COLORLESS", "R": "FIRE", "W": "WATER", "L": "LIGHTNING",
        "P": "PSYCHIC", "F": "FIGHTING", "D": "DARK", "M": "METAL",
        "G": "GRASS", "N": "DRAGON",
    }
    return mapping.get(et, "COLORLESS")


def _stage_from_api(api_data: dict) -> str:
    pa = api_data.get("pokemonAttr", {})
    stage = pa.get("stage", "Basic")
    mapping = {"Basic": "BASIC", "Stage 1": "STAGE_1", "Stage 2": "STAGE_2",
               "Restored": "RESTORED", "Baby": "BASIC"}
    return mapping.get(stage, "BASIC")


def _pokemon_rule_detect(api_data: dict) -> str:
    """Detect PokemonRule enum value."""
    name = api_data.get("nameEn", "") or ""
    name_cn = api_data.get("name", "") or ""
    combined = f"{name} {name_cn}".lower()
    if "tera" in combined:
        return "TERA"
    if "ancient" in combined:
        return "ANCIENT"
    if "future" in combined:
        return "FUTURE"
    if "radiant" in combined:
        return "RADIANT"
    return "NONE"


def _cost_from_api(cost: list[str]) -> str:
    """Convert API energy cost to CardType list."""
    mapping = {
        "Colorless": "COLORLESS", "Fire": "FIRE", "Water": "WATER",
        "Lightning": "LIGHTNING", "Psychic": "PSYCHIC", "Fighting": "FIGHTING",
        "Darkness": "DARK", "Metal": "METAL", "Grass": "GRASS",
        "Fairy": "FAIRY", "Dragon": "DRAGON",
    }
    return [mapping.get(c, "COLORLESS") for c in cost]


def _weakness_from_api(api_data: dict) -> list[str] | None:
    pa = api_data.get("pokemonAttr", {})
    w = pa.get("weakness")
    if not w:
        return None
    mapping = {"R": "FIRE", "W": "WATER", "L": "LIGHTNING", "P": "PSYCHIC",
               "F": "FIGHTING", "D": "DARK", "M": "METAL", "G": "GRASS", "C": "COLORLESS"}
    et = w.get("energy", "C")
    mapped = mapping.get(et, "COLORLESS")
    return [f"CardType.{mapped}"]


def _resistance_from_api(api_data: dict) -> list[str] | None:
    pa = api_data.get("pokemonAttr", {})
    r = pa.get("resistance")
    if not r:
        return None
    mapping = {"R": "FIRE", "W": "WATER", "L": "LIGHTNING", "P": "PSYCHIC",
               "F": "FIGHTING", "D": "DARK", "M": "METAL", "G": "GRASS", "C": "COLORLESS"}
    et = r.get("energy", "C")
    mapped = mapping.get(et, "COLORLESS")
    return [f"CardType.{mapped}"]


def generate_card_code(api_data: dict, card_info: dict) -> str:
    """Generate complete Python card class code."""
    name_en = api_data.get("nameEn", "Unknown")
    name_cn = api_data.get("name", name_en)
    set_code = card_info["setCodeEn"]
    number = card_info["cardIndexEn"]
    class_name = _make_class_name(name_en, set_code, number)
    card_type = api_data.get("cardType", "Pokemon")

    lines = [f'"""{name_en} - {set_code} {number}']
    lines.append("Auto-generated from tcg.mik.moe API.")
    lines.append('"""')

    if _is_pokemon(api_data):
        return _generate_pokemon_card(lines, class_name, api_data, card_info)
    elif "Energy" in card_type and "Special" not in card_type:
        return _generate_basic_energy(lines, class_name, api_data, card_info)
    elif card_type == "Special Energy":
        return _generate_special_energy(lines, class_name, api_data, card_info)
    elif card_type == "Item":
        return _generate_item_card(lines, class_name, api_data, card_info)
    elif card_type == "Supporter":
        return _generate_supporter_card(lines, class_name, api_data, card_info)
    elif card_type == "Stadium":
        return _generate_stadium_card(lines, class_name, api_data, card_info)
    elif card_type in ("Tool", "Pokémon Tool"):
        return _generate_tool_card(lines, class_name, api_data, card_info)
    else:
        return _generate_trainer_card(lines, class_name, api_data, card_info)


def _generate_pokemon_card(lines, class_name, api_data, card_info):
    """Generate PokemonCard subclass."""
    pa = api_data.get("pokemonAttr", {})
    hp = pa.get("hp", 70)
    stage = _stage_from_api(api_data)
    p_type = _card_type_from_api(api_data)
    rule = _pokemon_rule_detect(api_data)
    weakness = _weakness_from_api(api_data)
    resistance = _resistance_from_api(api_data)
    retreat = pa.get("retreatCost", 0) or 0
    evolves_from = pa.get("evolvesFrom", "")
    set_code = card_info["setCodeEn"]
    number = card_info["cardIndexEn"]
    name_cn = (api_data.get("name") or api_data.get("nameEn") or "").replace('"', '\\"')
    name_en = (api_data.get("nameEn") or "").replace('"', '\\"')

    # Determine prize count
    _name_lower = name_en.lower()
    if any(t in _name_lower for t in [" ex", " vstar", " vmax", " v-union", " gx"]):
        prize_count = 2
    elif " v " in _name_lower or _name_lower.endswith(" v"):
        prize_count = 2
    else:
        prize_count = 1
    lines.extend([
        "from ptcg.core.action import AttackAction, PlayPokemonAction, RetreatAction",
        "from ptcg.core.attack import Attack",
        "from ptcg.core.card import PokemonCard",
        "from ptcg.core.enums import (",
        "    CardType, PokemonPosition, PokemonRule, PokemonType, Stage,",
        ")",
        "from ptcg.core.reducer import (",
        "    reduce_attack_action, reduce_play_pokemon_action,",
        "    reduce_retreat_action,",
        ")",
        "from ptcg.utils.utils import check_energy, opponent_active",
        "",
        "",
        f"class {class_name}(PokemonCard):",
        f'    """{api_data.get("nameEn", "")} - {stage.title()} Pokemon. HP: {hp}."""',
        "    def __init__(self) -> None:",
        "        super().__init__()",
        f'        self.set_name = "{set_code}"',
        f'        self.number = "{number}"',
        f'        self.id = f"{{self.set_name}}-{{self.number}}"',
        f'        self.name = "{name_cn}"',
        "",
        "        # Pokémon attributes",
        f"        self.hp = {hp}",
        f"        self.pokemonType = PokemonType.NORMAL",
        f"        self.pokemonRule = PokemonRule.{rule}",
        f"        self.stage = Stage.{stage}",
        f"        self.cardType = CardType.{p_type}",
        "",
        "        # Retreat/Weakness/Resistance",
        f"        self.retreat = [CardType.COLORLESS] * {retreat}",
    ])

    if weakness:
        lines.append(f"        self.weakness = [{', '.join(weakness)}]")
    else:
        lines.append("        self.weakness = []")

    if resistance:
        lines.append(f"        self.resistance = [{', '.join(resistance)}]")
    else:
        lines.append("        self.resistance = []")

    if evolves_from:
        lines.append(f'        self.evolveFrom = ["{evolves_from}"]')
    else:
        lines.append("        self.evolveFrom = []")

    # Determine prize count
    _name_lower = name_en.lower()
    if any(t in _name_lower for t in [" ex", " vstar", " vmax", " v-union", " gx"]):
        prize_count = 2
    elif " v " in _name_lower or _name_lower.endswith(" v"):
        prize_count = 2
    else:
        prize_count = 1
    lines.extend([
        "        self.prize = 2" if rule == "EX" else "        self.prize = 1",
        "",
        "        # State",
        "        self.energy = []",
        "        self.attachment = []",
        "        self.evolved = []",
        "",
        "        # Attack definitions",
        "        self.attacks = [",
    ])

    for atk in attacks:
        atk_name = atk.get("name", "Unknown")
        cost_raw = atk.get("cost", [])
        cost = _cost_from_api(cost_raw) if cost_raw else ["CardType.COLORLESS"]
        dmg = atk.get("damage", 0) or 0
        text = atk.get("text", "")
        text = text[:200].replace('"', '\\"')
    # Determine prize count
    _name_lower = name_en.lower()
    if any(t in _name_lower for t in [" ex", " vstar", " vmax", " v-union", " gx"]):
        prize_count = 2
    elif " v " in _name_lower or _name_lower.endswith(" v"):
        prize_count = 2
    else:
        prize_count = 1
        lines.extend([
            "            Attack({",
            f'                "name": "{atk_name}",',
            f'                "damage": {dmg},',
            f'                "cost": [{", ".join(f"CardType.{c}" for c in cost)}],',
            f'                "text": "{text}",',
            "            }),",
        ])

    lines.append("        ]")

    # Abilities section (as comments for now)
    for ab in abilities:
        ab_name = ab.get("name", "")
        ab_text = ab.get("text", "")[:200]
        lines.append(f"        # Ability: {ab_name} — {ab_text}")

    # get_actions method
    # Determine prize count
    _name_lower = name_en.lower()
    if any(t in _name_lower for t in [" ex", " vstar", " vmax", " v-union", " gx"]):
        prize_count = 2
    elif " v " in _name_lower or _name_lower.endswith(" v"):
        prize_count = 2
    else:
        prize_count = 1
    lines.extend([
        "",
        "    def get_actions(self, state):",
        '        """Return list of currently available actions."""',
        "        actions = []",
        "",
        "        # If in active position, check if can attack",
        "        if self.position == PokemonPosition.ACTIVE:",
        "            for attack in self.attacks:",
        "                if check_energy(attack.cost, self.energy):",
        "                    targets = opponent_active(state)",
        "                    if targets:",
        "                        actions.append(AttackAction(state.turn, self, attack, targets[0]))",
        "                        break  # one attack per turn",
        "",
        "        return actions",
        "",
        "    def reduce_action(self, action, state):",
        '        """Handle action execution."""',
        "        if isinstance(action, PlayPokemonAction):",
        "            reduce_play_pokemon_action(action, state)",
        "        elif isinstance(action, AttackAction):",
        "            yield from reduce_attack_action(action, state)",
        "        elif isinstance(action, RetreatAction):",
        "            yield from reduce_retreat_action(action, state)",
    ])

    return "\n".join(lines)


def _generate_basic_energy(lines, class_name, api_data, card_info):
    """Generate EnergyCard for basic energy."""
    set_code = card_info["setCodeEn"]
    number = card_info["cardIndexEn"]
    name_en = api_data.get("nameEn", "")
    name_cn = api_data.get("name", name_en)

    # Determine energy type
    et_map = {
        "Grass Energy": "GRASS", "Fire Energy": "FIRE", "Water Energy": "WATER",
        "Lightning Energy": "LIGHTNING", "Psychic Energy": "PSYCHIC",
        "Fighting Energy": "FIGHTING", "Darkness Energy": "DARK",
        "Metal Energy": "METAL", "Fairy Energy": "FAIRY",
    }
    ctype = et_map.get(name_en, "COLORLESS")

    # Determine prize count
    _name_lower = name_en.lower()
    if any(t in _name_lower for t in [" ex", " vstar", " vmax", " v-union", " gx"]):
        prize_count = 2
    elif " v " in _name_lower or _name_lower.endswith(" v"):
        prize_count = 2
    else:
        prize_count = 1
    lines.extend([
        "from ptcg.core.action import AttachEnergyAction",
        "from ptcg.core.card import EnergyCard",
        "from ptcg.core.enums import CardType, EnergyType",
        "from ptcg.core.reducer import reduce_attach_energy_action",
        "from ptcg.utils.utils import can_attach_energy, current_all_pokemon",
        "",
        "",
        f"class {class_name}(EnergyCard):",
        '    """Basic Energy card."""',
        "    def __init__(self) -> None:",
        "        super().__init__()",
        f'        self.set_name = "{set_code}"',
        f'        self.number = "{number}"',
        f'        self.id = f"{{self.set_name}}-{{self.number}}"',
        f'        self.name = "{name_cn}"',
        f"        self.cardType = CardType.{ctype}",
        "        self.energyType = EnergyType.BASIC",
        f"        self.provides = [CardType.{ctype}]",
        "",
        "    def get_actions(self, state):",
        "        if not can_attach_energy(state):",
        "            return []",
        "        return [AttachEnergyAction(state.turn, self, p)",
        "                for p in current_all_pokemon(state)]",
        "",
        "    def reduce_action(self, action, state):",
        "        if isinstance(action, AttachEnergyAction):",
        "            reduce_attach_energy_action(action, state)",
    ])
    return "\n".join(lines)


def _generate_item_card(lines, class_name, api_data, card_info):
    """Generate ItemCard stub."""
    return _generate_simple_trainer(lines, class_name, api_data, card_info, "ItemCard")


def _generate_supporter_card(lines, class_name, api_data, card_info):
    return _generate_simple_trainer(lines, class_name, api_data, card_info, "SupporterCard")


def _generate_stadium_card(lines, class_name, api_data, card_info):
    return _generate_simple_trainer(lines, class_name, api_data, card_info, "StadiumCard")


def _generate_tool_card(lines, class_name, api_data, card_info):
    return _generate_simple_trainer(lines, class_name, api_data, card_info, "ToolCard")


def _generate_trainer_card(lines, class_name, api_data, card_info):
    return _generate_simple_trainer(lines, class_name, api_data, card_info, "TrainerCard")


def _generate_special_energy(lines, class_name, api_data, card_info):
    return _generate_simple_trainer(lines, class_name, api_data, card_info, "EnergyCard")


def _generate_simple_trainer(lines, class_name, api_data, card_info, base_class):
    """Generate a simple trainer card with minimal get_actions."""
    set_code = card_info["setCodeEn"]
    number = card_info["cardIndexEn"]
    name_cn = api_data.get("name", api_data.get("nameEn", ""))
    effect_text = api_data.get("description", "").strip()[:300]

    # Handle put-to-play actions for stadiums and tools
    if base_class == "StadiumCard":
        play_action = "PutStadiumAction"
        play_import = f"from ptcg.core.action import UseItemAction, {play_action}"
        reducer_import = ""
        get_actions_body = """        actions = []
        player = current_player(state)

        if not player.stadiumPlayedTurn and self in player.hand:
            actions.append(PutStadiumAction(player.id, self))

        return actions"""
        reduce_body = """        if isinstance(action, PutStadiumAction):
            if state.stadium:
                old_stadium = state.stadium[0]
                try:
                    result = old_stadium.reduce_action(
                        DiscardStadiumAction(old_stadium.playedFrom, old_stadium), state
                    )
                    if result is not None:
                        yield from result
                except StopIteration:
                    pass
            self.playedFrom = player.id
            player.stadiumPlayedTurn = True
            move_cards(
                action.source, (player.id, CardPosition.HAND), (None, CardPosition.STADIUM), state
            )"""
        extra_imports = [
            "from ptcg.core.action import DiscardStadiumAction",
            "from ptcg.utils.utils import current_player, move_cards",
        ]
    elif base_class == "ToolCard":
        play_action = "AttachToolAction"
        play_import = f"from ptcg.core.action import UseItemAction, AttachToolAction"
        reducer_import = ""
        get_actions_body = """        actions = []
        player = current_player(state)
        # Tool attachment is handled generically
        return actions"""
        reduce_body = """        pass"""
        extra_imports = ["from ptcg.utils.utils import current_player"]
    else:
        play_action = "UseItemAction"
        play_import = "from ptcg.core.action import UseItemAction"
        reducer_import = ""
        get_actions_body = """        actions = []
        player = current_player(state)
        actions.append(UseItemAction(player.id, self))
        return actions"""
        reduce_body = """        if isinstance(action, UseItemAction):
            player = current_player(state)
            # Move card to discard (generic handler)
            move_cards(
                self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state
            )"""
        extra_imports = []

    import_lines = [
        play_import,
        f"from ptcg.core.card import {base_class}",
        "from ptcg.core.enums import CardPosition, CardType, EnergyType, SuperType",
    ] + [i for i in extra_imports if i]
    import_lines.append("from ptcg.utils.utils import current_player")

    if base_class in ("ItemCard", "SupporterCard", "TrainerCard"):
        import_lines.append("from ptcg.utils.utils import move_cards")

    lines.extend(import_lines)
    # Determine prize count
    _name_lower = name_en.lower()
    if any(t in _name_lower for t in [" ex", " vstar", " vmax", " v-union", " gx"]):
        prize_count = 2
    elif " v " in _name_lower or _name_lower.endswith(" v"):
        prize_count = 2
    else:
        prize_count = 1
    lines.extend([
        "",
        "",
        f"class {class_name}({base_class}):",
        f'    """{api_data.get("nameEn", "")} - {base_class.replace("Card", "")}."""',
        "    def __init__(self):",
        "        super().__init__()",
        f'        self.set_name = "{set_code}"',
        f'        self.number = "{number}"',
        f'        self.id = f"{{self.set_name}}-{{self.number}}"',
        f'        self.name = "{name_cn}"',
        "        self.cardType = CardType.NONE",
    ])

    if effect_text:
        lines.append(f'        self.text = "{effect_text}"')

    # Determine prize count
    _name_lower = name_en.lower()
    if any(t in _name_lower for t in [" ex", " vstar", " vmax", " v-union", " gx"]):
        prize_count = 2
    elif " v " in _name_lower or _name_lower.endswith(" v"):
        prize_count = 2
    else:
        prize_count = 1
    lines.extend([
        "",
        "    def get_actions(self, state):",
        f"        {get_actions_body}",
        "",
        "    def reduce_action(self, action, state):",
        f"        {reduce_body}",
    ])

    return "\n".join(lines)


async def main():
    dry_run = "--dry-run" in sys.argv

    print("=== Bootstrap Missing Cards (v2) ===")
    sys.path.insert(0, str(Path(__file__).parent.parent))
    missing = get_missing_cards()
    print(f"Missing cards: {len(missing)}")

    if not missing:
        print("All cards registered!")
        return

    # Fetch API data
    print(f"\nFetching data ({CONCURRENCY} concurrent)...")
    connector = aiohttp.TCPConnector(limit=CONCURRENCY)
    async with aiohttp.ClientSession(connector=connector) as session:
        sem = asyncio.Semaphore(CONCURRENCY)

        async def fetch_one(card):
            async with sem:
                sc = card.get("setCode") or card["setCodeEn"]
                ci = card.get("cardIndex") or card["cardIndexEn"]
                detail = await fetch_card_detail(session, sc, ci)
                card["_detail"] = detail
                s = "OK" if detail else "FAIL"
                print(f"  [{s}] {card['_card_id']}: {card['nameEn']}")
                return card

        results = await asyncio.gather(*[fetch_one(c) for c in missing])

    success = sum(1 for r in results if r.get("_detail"))
    print(f"\nSuccess: {success}/{len(results)}")

    if dry_run:
        print("Dry run - not writing files.")
        return

    # Generate files
    created = 0
    for card in results:
        detail = card.get("_detail")
        if not detail:
            continue

        set_dir = CARDS_DIR / card["setCodeEn"]
        set_dir.mkdir(exist_ok=True)
        (set_dir / "__init__.py").touch()

        code = generate_card_code(detail, card)
        class_name = _make_class_name(card["nameEn"], card["setCodeEn"], card["cardIndexEn"])
        filename = class_name.lower() + ".py"
        filepath = set_dir / filename

        filepath.write_text(code, encoding="utf-8")
        created += 1

    print(f"\nCreated {created} files.")
    print("Next: implement effects in generated cards.")


if __name__ == "__main__":
    asyncio.run(main())
