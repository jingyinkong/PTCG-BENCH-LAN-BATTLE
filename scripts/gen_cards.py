#!/usr/bin/env python3
"""Minimal correct card generator from deck_data.json + API."""
import asyncio, json, sys, re, textwrap
from pathlib import Path
import aiohttp

API = "https://tcg.mik.moe/api/v3"
DECK_DATA = Path(__file__).parent.parent / "deck_data.json"
CARDS_DIR = Path(__file__).parent.parent / "ptcg" / "cards"
CONC = 8

ENUM_MAP = {"C": "COLORLESS", "R": "FIRE", "W": "WATER", "L": "LIGHTNING",
            "P": "PSYCHIC", "F": "FIGHTING", "D": "DARK", "M": "METAL",
            "G": "GRASS", "N": "DRAGON"}
STAGE_MAP = {"Basic": "BASIC", "Stage 1": "STAGE_1", "Stage 2": "STAGE_2",
             "Restored": "RESTORED", "Baby": "BASIC"}
WEAK_MAP = {"R": "FIRE", "W": "WATER", "L": "LIGHTNING", "P": "PSYCHIC",
            "F": "FIGHTING", "D": "DARK", "M": "METAL", "G": "GRASS", "C": "COLORLESS"}
E_MAP = {"Grass Energy": "GRASS", "Fire Energy": "FIRE", "Water Energy": "WATER",
         "Lightning Energy": "LIGHTNING", "Psychic Energy": "PSYCHIC",
         "Fighting Energy": "FIGHTING", "Darkness Energy": "DARK", "Metal Energy": "METAL"}


def cls_name(en_name, sc, num):
    c = re.sub(r'[^a-zA-Z0-9]', '', en_name.replace(" ", "").replace("-", "")
               .replace("'", "").replace(".", ""))
    c = c.replace("é", "e").replace("è", "e").replace("ê", "e")
    return f"{sc}{num}{c}"


def safe_str(s):
    if not s: return ""
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").replace("\r", "").replace("×", "x")[:300]


async def fetch(session, sc, ci):
    for _ in range(3):
        try:
            async with session.post(f"{API}/card/card-detail",
                json={"setCode": sc, "cardIndex": ci},
                timeout=aiohttp.ClientTimeout(total=15)) as r:
                d = await r.json()
                if d.get("code") == 200: return d["data"]
        except Exception: await asyncio.sleep(0.5)
    return None


def gen_pokemon(data, info):
    pa = data.get("pokemonAttr", {})
    hp = pa.get("hp", 70) or 70
    stage = STAGE_MAP.get(pa.get("stage", "Basic"), "BASIC")
    ctype = ENUM_MAP.get(pa.get("energyType", "C"), "COLORLESS")
    retreat = pa.get("retreatCost", 0) or 0
    w = pa.get("weakness")
    weakness = f"[CardType.{WEAK_MAP.get(w['energy'], 'COLORLESS')}]" if w else "[]"
    r = pa.get("resistance")
    resistance = f"[CardType.{WEAK_MAP.get(r['energy'], 'COLORLESS')}]" if r else "[]"
    ef = pa.get("evolvesFrom", "") or ""

    n = (data.get("nameEn") or "").lower()
    if "tera" in n: rule = "TERA"
    elif "ancient" in n: rule = "ANCIENT"
    elif "future" in n: rule = "FUTURE"
    elif "radiant" in n: rule = "RADIANT"
    else: rule = "NONE"

    if any(t in n for t in (" ex", " vstar", " vmax", " v-union", " gx")) or " v " in n or n.endswith(" v"):
        prize = 2
    else: prize = 1

    cn = safe_str(data.get("name") or data.get("nameEn") or "")
    en = safe_str(data.get("nameEn") or "")
    sc = info["setCodeEn"]; num = str(info["cardIndexEn"]).zfill(3)

    attacks_code = "[]"
    attacks_raw = pa.get("attack", [])
    if attacks_raw:
        parts = []
        for a in attacks_raw:
            aname = safe_str(a.get("name", ""))
            cr = a.get("cost", [])
            cost = [f'CardType.{ENUM_MAP.get(c, "COLORLESS")}' for c in cr] if cr else ["CardType.COLORLESS"]
            dmg_raw = a.get("damage", 0) or 0
            dmg = int(re.sub(r'[^0-9]', '', str(dmg_raw)) or '0')
            txt = safe_str(a.get("text", ""))
            parts.append(f'        Attack({{"name": "{aname}", "damage": {dmg}, "cost": [{", ".join(cost)}], "text": "{txt}"}})')
        attacks_code = "[\n" + ",\n".join(parts) + "\n        ]"

    return f'''"""{cn} - {sc} {num}"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, opponent_active


class {cls_name(en, sc, num)}(PokemonCard):
    """{cn} - {stage} 宝可梦。HP: {hp}。"""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "{sc}"
        self.number = "{num}"
        self.id = f"{{self.set_name}}-{{self.number}}"
        self.name = "{cn}"
        self.hp = {hp}
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.{rule}
        self.stage = Stage.{stage}
        self.cardType = CardType.{ctype}
        self.retreat = [CardType.COLORLESS] * {retreat}
        self.weakness = {weakness}
        self.resistance = {resistance}
        self.evolveFrom = {["" + ef + ""] if ef else []}
        self.prize = {prize}
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.attacks = {attacks_code}

    def get_actions(self, state):
        actions = []
        if self.position == PokemonPosition.ACTIVE:
            for attack in self.attacks:
                if check_energy(attack.cost, self.energy):
                    targets = opponent_active(state)
                    if targets:
                        actions.append(AttackAction(state.turn, self, attack, targets[0]))
                        break
        return actions

    def reduce_action(self, action, state):
        if isinstance(action, PlayPokemonAction):
            reduce_play_pokemon_action(action, state)
        elif isinstance(action, EvolvePokemonAction):
            reduce_evolve_pokemon_action(action, state)
        elif isinstance(action, AttackAction):
            yield from reduce_attack_action(action, state)
        elif isinstance(action, RetreatAction):
            yield from reduce_retreat_action(action, state)
'''


def gen_energy(data, info, special=False):
    cn = safe_str(data.get("name") or data.get("nameEn") or "")
    sc = info["setCodeEn"]; num = str(info["cardIndexEn"]).zfill(3)
    en = safe_str(data.get("nameEn") or "")
    ct = E_MAP.get(data.get("nameEn", ""), "COLORLESS")
    etype = "SPECIAL" if special else "BASIC"
    txt = safe_str(data.get("description") or "")
    text_line = f'\n        self.text = "{txt}"' if txt else ""
    return f'''"""{cn} - {sc} {num}"""
from ptcg.core.action import AttachEnergyAction
from ptcg.core.card import EnergyCard
from ptcg.core.enums import CardType, EnergyType
from ptcg.core.reducer import reduce_attach_energy_action
from ptcg.utils.utils import can_attach_energy, current_all_pokemon


class {cls_name(en, sc, num)}(EnergyCard):
    """{'特殊' if special else '基本'}能量卡。"""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "{sc}"
        self.number = "{num}"
        self.id = f"{{self.set_name}}-{{self.number}}"
        self.name = "{cn}"
        self.cardType = CardType.{ct}
        self.energyType = EnergyType.{etype}
        self.provides = [CardType.{ct}]{text_line}

    def get_actions(self, state):
        if not can_attach_energy(state):
            return []
        return [AttachEnergyAction(state.turn, self, p) for p in current_all_pokemon(state)]

    def reduce_action(self, action, state):
        if isinstance(action, AttachEnergyAction):
            reduce_attach_energy_action(action, state)
'''


def gen_trainer(data, info, base):
    cn = safe_str(data.get("name") or data.get("nameEn") or "")
    sc = info["setCodeEn"]; num = str(info["cardIndexEn"]).zfill(3)
    en = safe_str(data.get("nameEn") or "")
    txt = safe_str(data.get("description") or "")

    if base == "StadiumCard":
        imports = (
            "from ptcg.core.action import PutStadiumAction, DiscardStadiumAction\n"
            "from ptcg.core.card import StadiumCard\n"
            "from ptcg.core.enums import CardPosition, CardType\n"
            "from ptcg.utils.utils import current_player, move_cards"
        )
        ga = (
            "        actions = []\n"
            "        player = current_player(state)\n"
            "        if not player.stadiumPlayedTurn and self in player.hand:\n"
            "            actions.append(PutStadiumAction(player.id, self))\n"
            "        return actions"
        )
        ra = (
            "        player = current_player(state)\n"
            "        if isinstance(action, PutStadiumAction):\n"
            "            if state.stadium:\n"
            "                old = state.stadium[0]\n"
            "                try:\n"
            "                    r = old.reduce_action(DiscardStadiumAction(old.playedFrom, old), state)\n"
            "                    if r is not None:\n"
            "                        yield from r\n"
            "                except StopIteration:\n"
            "                    pass\n"
            "            self.playedFrom = player.id\n"
            "            player.stadiumPlayedTurn = True\n"
            "            move_cards(action.source, (player.id, CardPosition.HAND), (None, CardPosition.STADIUM), state)"
        )
    elif base == "SupporterCard":
        imports = (
            "from ptcg.core.action import UseSupporterAction\n"
            f"from ptcg.core.card import {base}\n"
            f"from ptcg.core.enums import CardPosition, CardType\n"
            f"from ptcg.utils.utils import current_player, move_cards"
        )
        ga = (
            "        actions = []\n"
            "        player = current_player(state)\n"
            "        if not player.supporterPlayedTurn:\n"
            "            actions.append(UseSupporterAction(state.turn, self))\n"
            "        return actions"
        )
        ra = (
            "        if isinstance(action, UseSupporterAction):\n"
            "            player = current_player(state)\n"
            "            move_cards(self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state)\n"
            "            player.supporterPlayedTurn = True"
        )
    else:
        imports = (
            f"from ptcg.core.action import UseItemAction\n"
            f"from ptcg.core.card import {base}\n"
            f"from ptcg.core.enums import CardPosition, CardType\n"
            f"from ptcg.utils.utils import current_player, move_cards"
        )
        ga = (
            "        actions = []\n"
            "        player = current_player(state)\n"
            "        actions.append(UseItemAction(player.id, self))\n"
            "        return actions"
        )
        ra = (
            "        if isinstance(action, UseItemAction):\n"
            "            player = current_player(state)\n"
            "            move_cards(self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state)"
        )

    type_cn = {"StadiumCard": "场地", "ItemCard": "道具", "SupporterCard": "支援者",
                "ToolCard": "宝可梦道具", "TrainerCard": "训练家"}.get(base, "训练家")
    return f'''"""{cn} - {sc} {num}"""
{imports}


class {cls_name(en, sc, num)}({base}):
    """{cn} - {type_cn}卡。"""
    def __init__(self):
        super().__init__()
        self.set_name = "{sc}"
        self.number = "{num}"
        self.id = f"{{self.set_name}}-{{self.number}}"
        self.name = "{cn}"
        self.cardType = CardType.NONE
        self.text = "{txt}"

    def get_actions(self, state):
{ga}

    def reduce_action(self, action, state):
{ra}
'''


def generate(data, info):
    ct = data.get("cardType", "")
    if ct in ("Pokemon", "Pokémon"): return gen_pokemon(data, info)
    elif "Special" in ct: return gen_energy(data, info, special=True)
    elif "Energy" in ct: return gen_energy(data, info)
    elif ct == "Item": return gen_trainer(data, info, "ItemCard")
    elif ct == "Supporter": return gen_trainer(data, info, "SupporterCard")
    elif ct == "Stadium": return gen_trainer(data, info, "StadiumCard")
    elif ct in ("Tool", "Pokémon Tool"): return gen_trainer(data, info, "ToolCard")
    else: return gen_trainer(data, info, "TrainerCard")


async def main():
    sys.path.insert(0, str(Path(__file__).parent.parent))
    with open(DECK_DATA) as f:
        ddata = json.load(f)
    from ptcg.core.card_registry import registry
    existing = set(registry.list_all())

    all_cards = {}
    for deck in ddata["decks"]:
        for c in deck.get("full_deck", []):
            k = (c["setCodeEn"], c["cardIndexEn"])
            if k not in all_cards:
                cid = f'{c["setCodeEn"]}-{str(c["cardIndexEn"]).zfill(3)}'
                # Check using normalized lookup
                if not registry.get_by_set_and_number(c["setCodeEn"], str(c["cardIndexEn"]).zfill(3)):
                    all_cards[k] = c

    missing = list(all_cards.values())
    print(f"Missing: {len(missing)}")

    if "--dry-run" in sys.argv:
        for c in missing[:10]:
            print(f"  {c['setCodeEn']}-{c['cardIndexEn']}: {c['nameEn']}")
        return

    connector = aiohttp.TCPConnector(limit=CONC)
    async with aiohttp.ClientSession(connector=connector) as s:
        sem = asyncio.Semaphore(CONC)

        async def one(c):
            async with sem:
                sc = c.get("setCode") or c["setCodeEn"]
                ci = c.get("cardIndex") or c["cardIndexEn"]
                d = await fetch(s, sc, ci)
                c["_d"] = d
                st = "OK" if d else "FAIL"
                print(f"  [{st}] {c['setCodeEn']}-{c['cardIndexEn']}: {c['nameEn']}")
                return c

        results = await asyncio.gather(*[one(c) for c in missing])

    created = 0
    for c in results:
        d = c.get("_d")
        if not d: continue
        sdir = CARDS_DIR / c["setCodeEn"]
        sdir.mkdir(exist_ok=True)
        (sdir / "__init__.py").touch()
        code = generate(d, c)
        fname = cls_name(safe_str(c["nameEn"]), c["setCodeEn"], c["cardIndexEn"]).lower() + ".py"
        fpath = sdir / fname
        fpath.write_text(code, encoding="utf-8")
        created += 1

    print(f"\nCreated {created} files.")
    # Verify
    from ptcg.core.card_registry import registry
    registry._loaded = False
    registry._ensure_loaded()
    new_count = len(registry.list_all())
    print(f"Registry now has {new_count} cards (was {len(existing)}).")


if __name__ == "__main__":
    asyncio.run(main())
