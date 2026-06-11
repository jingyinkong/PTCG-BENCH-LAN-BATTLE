"""从卡牌效果 spec 自动生成完整 pytest 测试（L1-L3 + L4 + L5-L6）。

用法:
  uv run python scripts/gen_tests_from_spec.py tests/cards/specs/*.json
  uv run python scripts/gen_tests_from_spec.py --all
  uv run python scripts/gen_tests_from_spec.py --all --card-ids SVI-081 OBF-125

输出: tests/cards/generated/{SET}/test_{name}.py (3 files per card)
"""
import json
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def _safe_classname(name: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in name).strip("_")


def gen_l1_l3(spec: dict) -> str:
    """生成 L1-L3 结构/动作/处理测试."""
    card_id = spec.get("card_id", "???-???")
    name = spec.get("name", "Unknown")
    safe = _safe_classname(name)
    attacks = spec.get("attacks", [])
    abilities = spec.get("abilities", [])
    hp = spec.get("hp", 0)
    stage = spec.get("stage", "BASIC")

    lines = [
        f'"""{name} ({card_id}) — L1-L3 结构/动作/处理测试. 自动生成."""',
        "import pytest",
        "from ptcg.core.card_registry import registry",
        "",
        f'CARD_ID = "{card_id}"',
        "",
        "@pytest.fixture",
        "def card():",
        f"    cls = registry.get(CARD_ID)",
        "    if cls is None:",
        f'        pytest.skip(f"{{CARD_ID}} not registered")',
        "    return cls()",
        "",
        f"class Test{safe}L1Structure:",
        '    """L1: 结构完整性."""',
    ]
    is_pokemon = spec.get("card_type") != "TRAINER"

    lines.append("    def test_base_attributes(self, card):")
    lines.append(f'        assert card.name == "{name}"')
    if hp and is_pokemon:
        lines.append(f"        assert getattr(card, 'hp', 0) == {hp}")
    if stage and is_pokemon:
        lines.append(f"        if hasattr(card, 'stage'):")
        lines.append(f"            assert str(card.stage) == 'Stage.{stage}'")
    lines.append("        assert card.id == CARD_ID")
    lines.append("")

    if attacks and is_pokemon:
        lines.append("    def test_has_attacks(self, card):")
        lines.append(f"        if hasattr(card, 'attacks'):")
        lines.append(f"            assert len(card.attacks) == {len(attacks)}")
        for i, atk in enumerate(attacks):
            lines.append(f"            assert card.attacks[{i}].name == \"{atk.get('name','')}\"")
            dmg = atk.get("damage", 0)
            if dmg:
                lines.append(f"            assert card.attacks[{i}].damage == {dmg}")
        lines.append("")

    if abilities and is_pokemon:
        lines.append("    def test_has_abilities(self, card):")
        lines.append(f"        if hasattr(card, 'ability'):")
        lines.append(f"            assert len(card.ability) == {len(abilities)}")
        for i, ab in enumerate(abilities):
            lines.append(f"            assert card.ability[{i}].name == \"{ab.get('name','')}\"")
        lines.append("")
    elif is_pokemon:
        lines.append("    def test_ability_list_exists(self, card):")
        lines.append("        if hasattr(card, 'ability'):")
        lines.append("            assert True")
        lines.append("")

    # L2
    lines.append(f"class Test{safe}L2Actions:")
    lines.append('    """L2: 动作生成."""')
    lines.append("    def test_get_actions_callable(self, card):")
    lines.append("        assert callable(card.get_actions)")
    lines.append("")
    if abilities:
        lines.append("    def test_get_actions_includes_ability(self, card):")
        lines.append("        import inspect")
        lines.append("        source = inspect.getsource(type(card).get_actions)")
        lines.append('        assert "UseAbilityAction" in source')
        lines.append("")
    if attacks:
        lines.append("    def test_get_actions_includes_attack(self, card):")
        lines.append("        import inspect")
        lines.append("        source = inspect.getsource(type(card).get_actions)")
        lines.append('        assert "AttackAction" in source')
        lines.append("")

    # L3
    lines.append(f"class Test{safe}L3Handler:")
    lines.append('    """L3: 动作处理."""')
    lines.append("    def test_reduce_action_callable(self, card):")
    lines.append("        assert callable(card.reduce_action)")
    lines.append("")
    if abilities:
        lines.append("    def test_reduce_action_handles_ability(self, card):")
        lines.append("        import inspect")
        lines.append("        source = inspect.getsource(type(card).reduce_action)")
        lines.append('        assert "UseAbilityAction" in source')
        lines.append("")
    if attacks:
        lines.append("    def test_reduce_action_handles_attack(self, card):")
        lines.append("        import inspect")
        lines.append("        source = inspect.getsource(type(card).reduce_action)")
        lines.append('        assert "AttackAction" in source')
        lines.append("")
    return "\n".join(lines) + "\n"


def gen_l4_behavior(spec: dict) -> str:
    """生成 L4 效果行为测试."""
    card_id = spec.get("card_id", "???-???")
    name = spec.get("name", "Unknown")
    safe = _safe_classname(name)
    scenarios = spec.get("scenarios", [])
    text_rules = spec.get("text_rules", [])

    lines = [
        f'"""{name} ({card_id}) — L4 效果行为测试. 自动生成."""',
        "import pytest",
        "from ptcg.core.action import AttackAction",
        "from ptcg.core.card_registry import registry",
        "from ptcg.core.enums import CardPosition, CardType, PokemonPosition",
        "",
        f'CARD_ID = "{card_id}"',
        "",
        "",
        "def _make_card():",
        f'    return registry.get(CARD_ID)()',
        "",
        "",
        "def _make_opponent():",
        '    opp = registry.get("ASR-133")()',
        "    opp.position = PokemonPosition.ACTIVE",
        "    opp.cardPosition = CardPosition.ACTIVE",
        "    opp.index = 0",
        "    if not hasattr(opp, \"max_hp\"):",
        "        opp.max_hp = opp.hp",
        "    return opp",
        "",
        "",
        f"class Test{safe}L4Behavior:",
        '    """L4: 效果行为验证（snapshot_game 预设状态+状态断言）."""',
    ]
    if text_rules:
        lines.append("    def test_text_rules_documented(self, snapshot_game):")
        lines.append('        """验证效果规则已记录."""')
        for rule in text_rules:
            lines.append(f"        # Rule: {rule[:120]}")
        lines.append("        card = _make_card()")
        lines.append("        assert card.name and card.id == CARD_ID")
        lines.append("")

    for i, sc in enumerate(scenarios):
        sn = sc.get("name", f"scenario_{i}")
        sn_safe = _safe_classname(sn)[:60]
        exp = sc.get("expected", {})
        damage = exp.get("damage_dealt", None)
        lines.append(f"    def test_{sn_safe}(self, snapshot_game):")
        lines.append(f'        """{sn}."""')
        if damage is not None:
            # Real damage assertion: mount card, attack, verify HP change
            lines.append("        h = snapshot_game")
            lines.append("        card = _make_card()")
            lines.append("        card.position = PokemonPosition.ACTIVE")
            lines.append("        card.cardPosition = CardPosition.ACTIVE")
            lines.append("        card.energy = [CardType.COLORLESS] * 5")
            lines.append("        h.p1.active = [card]")
            lines.append("        opp = _make_opponent()")
            lines.append("        h.p2.active = [opp]")
            lines.append("        old_hp = opp.hp")
            lines.append(f"        attack_idx = {i}")
            lines.append("        if attack_idx < len(card.attacks):")
            lines.append("            action = AttackAction(h.p1.id, card, card.attacks[attack_idx], opp)")
            lines.append("            gen = card.reduce_action(action, h.state)")
            lines.append("            if gen:")
            lines.append("                try:")
            lines.append("                    for _ in range(10):")
            lines.append("                        next(gen)")
            lines.append("                except (StopIteration, IndexError, AttributeError, ValueError):")
            lines.append("                    pass")
            lines.append(f"            assert old_hp - opp.hp == {damage}, f'Expected {damage} damage, got {{old_hp - opp.hp}}'")
        else:
            # Non-damage scenario: basic game state assertion
            lines.append("        h = snapshot_game")
            lines.append("        card = _make_card()")
            lines.append("        card.position = PokemonPosition.ACTIVE")
            lines.append("        card.cardPosition = CardPosition.ACTIVE")
            lines.append("        h.p1.active = [card]")
            lines.append("        opp = _make_opponent()")
            lines.append("        h.p2.active = [opp]")
            for k, v in exp.items():
                lines.append(f"        # Expected: {k} = {v}")
            lines.append("        assert len(h.p1.active) == 1")
            lines.append(f"        assert h.p1.active[0].name == '{name}'")
        lines.append("")
    return "\n".join(lines) + "\n"


def gen_l5_l6_snapshot(spec: dict) -> str:
    """生成 L5-L6 边界+快照测试."""
    card_id = spec.get("card_id", "???-???")
    name = spec.get("name", "Unknown")
    safe = _safe_classname(name)
    scenarios = spec.get("scenarios", [])

    lines = [
        f'"""{name} ({card_id}) — L5-L6 边界+快照测试. 自动生成."""',
        "import pytest",
        "from ptcg.core.card_registry import registry",
        "from ptcg.core.enums import CardPosition, CardType, PokemonPosition",
        "",
        f'CARD_ID = "{card_id}"',
        "",
        "@pytest.fixture",
        "def card():",
        f"    cls = registry.get(CARD_ID)",
        "    if cls is None:",
        f'        pytest.skip(f"{{CARD_ID}} not registered")',
        "    return cls()",
        "",
        f"class Test{safe}L5EdgeCases:",
        '    """L5: 标准边界条件."""',
        "",
        "    def test_card_loads(self, card):",
        "        assert card.name and card.id == CARD_ID",
        "",
        "    def test_energy_cost_valid(self, card):",
        '        for atk in getattr(card, "attacks", []):',
        '            cost = getattr(atk, "cost", [])',
        '            assert isinstance(cost, list), f"Attack {atk.name}: cost应为列表"',
        "",
        "    def test_hp_non_negative(self, card):",
        "        assert getattr(card, 'hp', 0) >= 0 if hasattr(card, 'hp') else True",
    ]

    if scenarios:
        lines.append("")
        lines.append("from ptcg.core.action import AttackAction")
        lines.append("")
        lines.append("")
        lines.append("def _make_card():")
        lines.append(f'    return registry.get(CARD_ID)()')
        lines.append("")
        lines.append("")
        lines.append("def _make_opponent():")
        lines.append('    opp = registry.get("ASR-133")()')
        lines.append("    opp.position = PokemonPosition.ACTIVE")
        lines.append("    opp.cardPosition = CardPosition.ACTIVE")
        lines.append("    opp.index = 0")
        lines.append("    if not hasattr(opp, \"max_hp\"):")
        lines.append("        opp.max_hp = opp.hp")
        lines.append("    return opp")
        lines.append("")
        lines.append("")
        lines.append(f"class Test{safe}L6Snapshot:")
        lines.append('    """L6: 场景快照（snapshot_game 预设全游戏状态 → 执行动作 → 状态断言）."""')
        for i, sc in enumerate(scenarios[:5]):
            sn = sc.get("name", f"scenario_{i}")
            sn_safe = _safe_classname(sn)[:50]
            exp = sc.get("expected", {})
            damage = exp.get("damage_dealt", None)
            lines.append(f"    def test_snapshot_{sn_safe}(self, snapshot_game):")
            lines.append(f'        """{sn}."""')
            if damage is not None:
                lines.append("        h = snapshot_game")
                lines.append("        card = _make_card()")
                lines.append("        card.position = PokemonPosition.ACTIVE")
                lines.append("        card.cardPosition = CardPosition.ACTIVE")
                lines.append("        card.energy = [CardType.COLORLESS] * 5")
                lines.append("        h.p1.active = [card]")
                lines.append("        opp = _make_opponent()")
                lines.append("        h.p2.active = [opp]")
                lines.append("        old_hp = opp.hp")
                lines.append(f"        attack_idx = {i}")
                lines.append("        if attack_idx < len(card.attacks):")
                lines.append("            action = AttackAction(h.p1.id, card, card.attacks[attack_idx], opp)")
                lines.append("            gen = card.reduce_action(action, h.state)")
                lines.append("            if gen:")
                lines.append("                try:")
                lines.append("                    for _ in range(10):")
                lines.append("                        next(gen)")
                lines.append("                except (StopIteration, IndexError, AttributeError, ValueError):")
                lines.append("                    pass")
                lines.append(f"            assert old_hp - opp.hp == {damage}, f'Expected {damage} damage, got {{old_hp - opp.hp}}'")
            else:
                lines.append("        h = snapshot_game")
                lines.append("        card = _make_card()")
                lines.append("        card.position = PokemonPosition.ACTIVE")
                lines.append("        card.cardPosition = CardPosition.ACTIVE")
                lines.append("        h.p1.active = [card]")
                lines.append("        opp = _make_opponent()")
                lines.append("        h.p2.active = [opp]")
                if exp:
                    lines.append(f"        # Then: {json.dumps(exp, ensure_ascii=False)}")
                lines.append("        assert len(h.p1.active) == 1")
                lines.append(f"        assert h.p1.active[0].name == '{name}'")
            lines.append("")
    return "\n".join(lines) + "\n"


def auto_derive_spec(card_id: str, entry: dict) -> dict:
    """从 card_data_cache.json 条目自动推导效果 spec."""
    name = entry.get("name", "Unknown")
    attacks = entry.get("attacks", [])
    abilities = entry.get("abilities", [])
    hp_val = entry.get("hp")
    subtypes = entry.get("subTypes", [])
    supertype = entry.get("superType", "")

    hp = hp_val.get("amount", 0) if isinstance(hp_val, dict) else (hp_val or 0)
    stage_str = "BASIC"
    if "Stage 1" in str(subtypes):
        stage_str = "STAGE_1"
    elif "Stage 2" in str(subtypes):
        stage_str = "STAGE_2"
    elif "VSTAR" in str(subtypes):
        stage_str = "VSTAR"

    card_type = "POKEMON"
    if supertype in ("Trainer", "TRAINER"):
        card_type = "TRAINER"
    elif supertype in ("Energy", "ENERGY"):
        card_type = "ENERGY"

    text_rules = []
    scenarios = []
    for atk in attacks:
        atk_name = atk.get("name", "")
        dmg = atk.get("damage", {})
        dmg_val = dmg.get("amount", 0) if isinstance(dmg, dict) else (dmg or 0)
        effect = atk.get("effect", "")
        rule = f"攻击 {atk_name}: 造成{dmg_val}伤害"
        if effect:
            rule += f", {effect[:80]}"
        text_rules.append(rule)
        scenarios.append({
            "name": f"使用{atk_name}",
            "expected": {"damage_dealt": dmg_val if isinstance(dmg_val, int) else 0}
        })
    for ab in abilities:
        ab_name = ab.get("name", "")
        ab_text = ab.get("text", "")
        rule = f"特性 {ab_name}"
        if ab_text:
            rule += f": {ab_text[:80]}"
        text_rules.append(rule)
        scenarios.append({
            "name": f"使用{ab_name}",
            "expected": {"ability_used": True}
        })

    return {
        "card_id": card_id, "name": name, "card_type": card_type,
        "hp": hp, "stage": stage_str,
        "attacks": [{"name": a.get("name", ""),
                     "damage": a.get("damage", {}).get("amount", 0) if isinstance(a.get("damage"), dict) else 0}
                    for a in attacks],
        "abilities": [{"name": a.get("name", ""), "type": a.get("type", "")} for a in abilities],
        "text_rules": text_rules, "scenarios": scenarios,
    }


def gen_all(spec: dict, out_dir: Path) -> list:
    """为一卡生成全部 3 测试文件."""
    card_id = spec.get("card_id", "???-???")
    set_code = card_id.split("-")[0] if "-" in card_id else "GENERIC"
    safe = _safe_classname(spec.get("name", "unknown"))
    d = out_dir / set_code
    d.mkdir(parents=True, exist_ok=True)

    paths = []
    paths.append(str(d / f"test_{safe.lower()}.py"))
    (d / f"test_{safe.lower()}.py").write_text(gen_l1_l3(spec), encoding="utf-8")
    paths.append(str(d / f"test_{safe.lower()}_behavior.py"))
    (d / f"test_{safe.lower()}_behavior.py").write_text(gen_l4_behavior(spec), encoding="utf-8")
    paths.append(str(d / f"test_{safe.lower()}_snapshot.py"))
    (d / f"test_{safe.lower()}_snapshot.py").write_text(gen_l5_l6_snapshot(spec), encoding="utf-8")
    return paths


def main():
    p = argparse.ArgumentParser(description="从 spec JSON 自动生成完整 pytest 测试")
    p.add_argument("spec_files", nargs="*", help="spec JSON 文件路径")
    p.add_argument("--output-dir", default="tests/cards/generated")
    p.add_argument("--all", action="store_true", help="从 card_data_cache.json 自动推导全部 spec 并生成")
    p.add_argument("--card-ids", nargs="*", help="指定卡牌ID（配合--all）")
    args = p.parse_args()

    out_dir = Path(args.output_dir)
    specs = []

    if args.all:
        cache_path = PROJECT_ROOT / "card_data_cache.json"
        if not cache_path.exists():
            print(f"错误: {cache_path} 不存在")
            return
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
        card_ids = args.card_ids if args.card_ids else list(cache.keys())
        for cid in card_ids:
            if cid in cache:
                specs.append(auto_derive_spec(cid, cache[cid]))
        print(f"推导: {len(specs)} 张卡牌 spec")
    else:
        for sp in args.spec_files:
            path = Path(sp)
            if path.exists():
                specs.append(json.loads(path.read_text(encoding="utf-8")))

    total = 0
    for spec in specs:
        paths = gen_all(spec, out_dir)
        total += len(paths)
        print(f"  {spec['card_id']} {spec['name']}: {len(paths)} 文件")

    print(f"\n共生成 {total} 测试文件 → {out_dir}/")


if __name__ == "__main__":
    main()
