"""从卡牌效果 spec 生成 pytest 测试骨架。

用法: uv run python scripts/gen_tests_from_spec.py tests/cards/specs/*.json
输出: tests/cards/generated/test_{spec_name}.py
"""
import json
import argparse
from pathlib import Path


def gen(spec: dict) -> str:
    card_id = spec.get("card_id", "???-???")
    name = spec.get("name", "Unknown")
    rules = spec.get("text_rules", [])
    scenarios = spec.get("scenarios", [])
    safe = "".join(c if c.isalnum() else "_" for c in name).strip("_")
    out = [
        f'"""Auto-generated test skeleton for {name} ({card_id})."""',
        'import pytest',
        'from ptcg.core.card_registry import registry',
        '',
        'def make_card():',
        f'    c = registry.get("{card_id}")',
        '    if c is None:',
        f'        pytest.skip("{card_id} not registered")',
        '    return c()',
        '',
        f'class Test{safe}SpecRules:',
    ]
    if rules:
        out.append('    def test_text_rules_present(self):')
        out.append('        card = make_card()')
        for r in rules:
            out.append(f'        # Rule: {r[:80]}')
        out.append('        assert getattr(card, "text", None) or getattr(card, "name", None)  # Card exists')
        out.append('')
    methods = []
    for i, s in enumerate(scenarios):
        sn = s.get("name", f"scenario_{i}")
        sn_safe = "".join(c if c.isalnum() else "_" for c in sn).strip("_")[:60]
        exp = s.get("expected", {})
        methods.append(f'    @pytest.mark.skip(reason="Auto-generated — needs manual setup")')
        methods.append(f'    def test_{sn_safe}(self, snapshot_game):')
        methods.append(f'        """{sn}"""')
        methods.append('        h = snapshot_game')
        methods.append('        card = make_card()')
        methods.extend(f'        # Expected: {k} = {v}' for k, v in exp.items())
        methods.append('        # TODO: h.set_hand(...), set_deck(...), execute action, assert')
        methods.append('')
    if methods:
        out.append(f'class Test{safe}SpecScenarios:')
        out.extend(methods)
    return "\n".join(out) + "\n"


def main():
    p = argparse.ArgumentParser(description="从 spec JSON 生成 pytest 测试骨架")
    p.add_argument("spec_files", nargs="+")
    p.add_argument("--output-dir", default="tests/cards/generated")
    args = p.parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    for sp in args.spec_files:
        path = Path(sp)
        if not path.exists():
            print(f"跳过: {path}")
            continue
        spec = json.loads(path.read_text())
        code = gen(spec)
        out_path = out_dir / f"test_{path.stem}.py"
        out_path.write_text(code)
        n += 1
        print(f"生成: {out_path} ({len(spec.get('scenarios',[]))} 场景)")
    print(f"共 {n} 个 → {out_dir}/")


if __name__ == "__main__":
    main()
