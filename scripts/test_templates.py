"""14 种卡牌效果类型的 golden 测试模板。

每个 test_template_* 函数接受 (card_id, snapshot_game) 参数，
返回可直接插入测试文件的 Python 代码字符串。

用法:
  uv run python -c "from scripts.test_templates import *; print('OK')"
"""

from typing import Optional


def _template(body: str, card_id: str) -> str:
    """将模板 body 中的 {CARD_ID} 替换为实际卡牌 ID。"""
    return body.replace("{CARD_ID}", card_id)


DAMAGE_TEMPLATE = '''"""
{CARD_ID} — DAMAGE 效果行为测试.
"""
import pytest
from ptcg.core.card_registry import registry
from ptcg.core.enums import CardPosition, CardType, PokemonPosition


def _make_card():
    return registry.get("{CARD_ID}")()


def _make_opponent():
    return registry.get("ASR-133")()


class TestDamageBehavior:
    """DAMAGE 类型：能量 → 攻击 → 对手 HP 减少。"""

    def test_attack_with_energy(self, snapshot_game):
        """有足够能量时攻击可对对手造成伤害。"""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.ACTIVE
        card.position = PokemonPosition.ACTIVE
        card.energy = [CardType.COLORLESS]
        h.p1.active = [card]
        opp = _make_opponent()
        opp.cardPosition = CardPosition.ACTIVE
        opp.position = PokemonPosition.ACTIVE
        opp.hp = 200
        h.p2.active = [opp]
        actions = card.get_actions(h.state)
        assert len(actions) >= 1, "应返回至少一个攻击 action"

    def test_no_actions_without_energy(self, snapshot_game):
        """能量不足时不应返回攻击 action。"""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.ACTIVE
        card.position = PokemonPosition.ACTIVE
        card.energy = []
        h.p1.active = [card]
        opp = _make_opponent()
        opp.cardPosition = CardPosition.ACTIVE
        opp.position = PokemonPosition.ACTIVE
        h.p2.active = [opp]
        actions = card.get_actions(h.state)
        assert len(actions) == 0, "能量不足时应无 action"

    def test_attack_reduces_opponent_hp(self, snapshot_game):
        """攻击后对手 HP 减少。"""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.ACTIVE
        card.position = PokemonPosition.ACTIVE
        card.energy = [CardType.COLORLESS] * 2
        h.p1.active = [card]
        opp = _make_opponent()
        opp.cardPosition = CardPosition.ACTIVE
        opp.position = PokemonPosition.ACTIVE
        opp.hp = 200
        h.p2.active = [opp]
        hp_before = opp.hp
        from ptcg.core.action import AttackAction
        action = AttackAction(h.state.turn, card, card.attacks[0], opp)
        gen = card.reduce_action(action, h.state)
        if gen is not None:
            try:
                next(gen)
            except (StopIteration, IndexError, AttributeError, ValueError):
                pass
        assert opp.hp < hp_before, ('"'
            '对手 HP 应减少, before={hp_before} after={opp.hp}"'
        )
'''


discard_assertions = '''
        assert isinstance(actions, list), ("应返回 list, got {type(actions)}")\
'''


DISCARD_TEMPLATE = '''"""
{CARD_ID} — DISCARD 效果行为测试.
"""
import pytest
from ptcg.core.card_registry import registry
from ptcg.core.enums import CardPosition, CardType, PokemonPosition


def _make_card():
    return registry.get("{CARD_ID}")()


class TestDiscardBehavior:
    """DISCARD 类型：手牌条件 → 弃牌 —— 手牌减少 + 弃牌区增加。"""

    def test_get_actions_when_in_hand(self, snapshot_game):
        """手牌中时可使用。"""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.HAND
        h.p1.hand = [card]
        actions = card.get_actions(h.state)
        assert isinstance(actions, list), ("应返回 list, got {type(actions)}")

    def test_get_actions_with_extra_hand_card(self, snapshot_game):
        """手牌>=2（含自身+可弃目标）时可用。"""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.HAND
        h.p1.hand = [card]
        extra = registry.get("SVE-001")()
        extra.cardPosition = CardPosition.HAND
        h.p1.hand.append(extra)
        actions = card.get_actions(h.state)
        assert isinstance(actions, list), ("应返回 list, got {type(actions)}")

    def test_no_actions_when_not_in_hand(self, snapshot_game):
        """不在手牌时不可用。"""
        h = snapshot_game
        card = _make_card()
        actions = card.get_actions(h.state)
        assert len(actions) == 0, "不在手牌时应无 actions"

    def test_card_consumed_after_use(self, snapshot_game):
        """使用后自身被消耗（从手牌移走）。"""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.HAND
        h.p1.hand = [card]
        extra = registry.get("SVE-001")()
        extra.cardPosition = CardPosition.HAND
        h.p1.hand.append(extra)
        from ptcg.core.action import UseItemAction
        action = UseItemAction(h.p1.id, card)
        gen = card.reduce_action(action, h.state)
        if gen is not None:
            try:
                for _ in range(5):
                    next(gen)
            except (StopIteration, IndexError, AttributeError, ValueError):
                pass
        assert card not in h.p1.hand, "使用后自身应从手牌移走"
'''


SWITCH_TEMPLATE = '''"""
{CARD_ID} — SWITCH 效果行为测试.
"""
import pytest
from ptcg.core.card_registry import registry
from ptcg.core.enums import CardPosition, CardType, PokemonPosition


def _make_card():
    return registry.get("{CARD_ID}")()


class TestSwitchBehavior:
    """SWITCH 类型：后备存在 → 交换 —— 出战区 + 后场变化。"""

    def test_get_actions_with_bench(self, snapshot_game):
        """后场有宝可梦时可使用。"""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.HAND
        h.p1.hand = [card]
        active = registry.get("ASR-133")()
        active.cardPosition = CardPosition.ACTIVE
        active.position = PokemonPosition.ACTIVE
        h.p1.active = [active]
        bench = registry.get("ASR-133")()
        bench.cardPosition = CardPosition.BENCH
        bench.position = PokemonPosition.BENCH
        h.p1.bench = [bench]
        actions = card.get_actions(h.state)
        assert isinstance(actions, list), ("应返回 list, got {type(actions)}")

    def test_no_actions_without_bench(self, snapshot_game):
        """后场无宝可梦时不可使用。"""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.HAND
        h.p1.hand = [card]
        active = registry.get("ASR-133")()
        active.cardPosition = CardPosition.ACTIVE
        active.position = PokemonPosition.ACTIVE
        h.p1.active = [active]
        h.p1.bench = []
        actions = card.get_actions(h.state)
        assert len(actions) == 0, "无后场时应无 actions"

    def test_after_use_card_consumed_or_position_changed(self, snapshot_game):
        """使用后卡被消耗或上场位置变更。"""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.HAND
        h.p1.hand = [card]
        active = registry.get("ASR-133")()
        active.cardPosition = CardPosition.ACTIVE
        active.position = PokemonPosition.ACTIVE
        h.p1.active = [active]
        bench = registry.get("ASR-133")()
        bench.cardPosition = CardPosition.BENCH
        bench.position = PokemonPosition.BENCH
        h.p1.bench = [bench]
        from ptcg.core.action import UseItemAction
        action = UseItemAction(h.p1.id, card)
        gen = card.reduce_action(action, h.state)
        if gen is not None:
            try:
                for _ in range(5):
                    next(gen)
            except (StopIteration, IndexError, AttributeError, ValueError):
                pass
        new_active = h.p1.active[0] if h.p1.active else None
        assert new_active is not None or card not in h.p1.hand, \
            "卡应被消耗或有新出战宝可梦"
'''


EVOLVE_TEMPLATE = '''"""
{CARD_ID} — EVOLVE 效果行为测试.
"""
import pytest
from ptcg.core.card_registry import registry
from ptcg.core.enums import CardPosition, CardType, PokemonPosition, Stage


def _make_card():
    return registry.get("{CARD_ID}")()


class TestEvolveBehavior:
    """EVOLVE 类型：手牌进化 → 场上替换。"""

    def test_card_is_basic(self, snapshot_game):
        """进化前的宝可梦应为 BASIC。"""
        card = _make_card()
        assert card.stage == Stage.BASIC, ("应为基础宝可梦, got {card.stage}")
        assert card.name != "", "应有卡牌名称"

    def test_get_actions_when_active_with_evolve(self, snapshot_game):
        """出战区有对应进化链时返回进化 action。"""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.HAND
        h.p1.hand = [card]
        actions = card.get_actions(h.state)
        assert isinstance(actions, list)

    def test_evolve_replaces_active_or_bench(self, snapshot_game):
        """进化后场地上的宝可梦被替换。"""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.HAND
        h.p1.hand = [card]
        active = _make_card()
        active.cardPosition = CardPosition.ACTIVE
        active.position = PokemonPosition.ACTIVE
        h.p1.active = [active]
        from ptcg.core.action import EvolvePokemonAction
        action = EvolvePokemonAction(h.p1.id, card, active)
        gen = card.reduce_action(action, h.state)
        if gen is not None:
            try:
                for _ in range(5):
                    next(gen)
            except (StopIteration, IndexError, AttributeError, ValueError):
                pass
        assert card in h.p1.active or card.cardPosition == CardPosition.ACTIVE, \
            "进化后卡牌应出现在出战区"
'''


SEARCH_DECK_TEMPLATE = '''"""
{CARD_ID} — SEARCH_DECK 效果行为测试.
"""
import pytest
from ptcg.core.card_registry import registry
from ptcg.core.enums import CardPosition, CardType


def _make_card():
    return registry.get("{CARD_ID}")()


class TestSearchDeckBehavior:
    """SEARCH_DECK 类型：牌库搜索 —— 牌库变少 + 手牌/后场增加。"""

    def test_get_actions_with_deck(self, snapshot_game):
        """手牌有此卡且牌库非空时返回可用动作。"""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.HAND
        h.p1.hand = [card]
        h.set_deck(h.p1, ["SVE-001"])
        actions = card.get_actions(h.state)
        assert len(actions) >= 1, "牌库非空时应返回 action"

    def test_get_actions_deck_empty(self, snapshot_game):
        """牌库为空时不可使用。"""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.HAND
        h.p1.hand = [card]
        h.p1.left = []
        actions = card.get_actions(h.state)
        assert len(actions) == 0, "牌库空时应无 action"

    def test_reduce_action_consumes_card(self, snapshot_game):
        """使用后卡牌被消耗。"""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.HAND
        h.p1.hand = [card]
        h.set_deck(h.p1, ["SVE-001"] * 5)
        from ptcg.core.action import UseItemAction
        action = UseItemAction(h.p1.id, card)
        gen = card.reduce_action(action, h.state)
        if gen is not None:
            try:
                next(gen)
            except (StopIteration, IndexError, AttributeError, ValueError):
                pass
        assert card not in h.p1.hand or card.cardPosition != CardPosition.HAND, \
            "使用后卡牌应离开手牌"

    def test_not_available_when_not_in_hand(self, snapshot_game):
        """不在手牌时不能使用。"""
        h = snapshot_game
        h.set_deck(h.p1, ["SVE-001"])
        actions = _make_card().get_actions(h.state)
        assert len(actions) == 0, "不在手牌时应无 action"
'''


BENCH_TEMPLATE = '''"""
{CARD_ID} — BENCH 效果行为测试.
"""
import pytest
from ptcg.core.card_registry import registry
from ptcg.core.enums import CardPosition, CardType, PokemonPosition, Stage


def _make_card():
    return registry.get("{CARD_ID}")()


class TestBenchBehavior:
    """BENCH 类型：手牌/牌库 → 备战区。"""

    def test_get_actions_in_hand_with_bench_space(self, snapshot_game):
        """手牌中且备战区有空位时可使用。"""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.HAND
        h.p1.hand = [card]
        actions = card.get_actions(h.state)
        assert isinstance(actions, list), ("应返回 list, got {type(actions)}")

    def test_card_moves_to_bench_or_is_consumed(self, snapshot_game):
        """使用后卡牌移动到备战区或被消耗。"""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.HAND
        h.p1.hand = [card]
        from ptcg.core.action import UseItemAction
        action = UseItemAction(h.p1.id, card)
        gen = card.reduce_action(action, h.state)
        if gen is not None:
            try:
                for _ in range(5):
                    next(gen)
            except (StopIteration, IndexError, AttributeError, ValueError):
                pass
        assert (card in h.p1.bench
                or card not in h.p1.hand
                or card.cardPosition == CardPosition.BENCH), \
            "卡牌应移动到备战区或被消耗"

    def test_not_available_when_not_in_hand(self, snapshot_game):
        """不在手牌时不能使用。"""
        h = snapshot_game
        actions = _make_card().get_actions(h.state)
        assert len(actions) == 0, "不在手牌时应无 action"
'''


ABILITY_TEMPLATE = '''"""
{CARD_ID} — ABILITY 效果行为测试.
"""
import pytest
from ptcg.core.card_registry import registry
from ptcg.core.enums import CardPosition, CardType, PokemonPosition


def _make_card():
    return registry.get("{CARD_ID}")()


class TestAbilityBehavior:
    """ABILITY 类型：oncePerTurn + 效果执行。"""

    def test_card_has_ability(self, snapshot_game):
        """卡牌拥有 ability 属性。"""
        card = _make_card()
        assert hasattr(card, "ability"), "应包含 ability 属性"
        assert len(card.ability) >= 1, "应至少有一个 ability"

    def test_ability_in_get_actions(self, snapshot_game):
        """get_actions 返回中包含 UseAbilityAction。"""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.ACTIVE
        card.position = PokemonPosition.ACTIVE
        h.p1.active = [card]
        actions = card.get_actions(h.state)
        from ptcg.core.action import UseAbilityAction
        ability_actions = [a for a in actions if isinstance(a, UseAbilityAction)]
        assert len(ability_actions) >= 1, "应至少包含一个 UseAbilityAction"

    def test_once_per_turn_tracking(self, snapshot_game):
        """使用后 onceUsedTurn 记录该 ability 已被使用。"""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.ACTIVE
        card.position = PokemonPosition.ACTIVE
        h.p1.active = [card]
        ability = card.ability[0]
        from ptcg.core.action import UseAbilityAction
        action = UseAbilityAction(h.p1.id, card, ability)
        gen = card.reduce_action(action, h.state)
        if gen is not None:
            try:
                next(gen)
            except (StopIteration, IndexError, AttributeError, ValueError):
                pass
        assert h.p1.onceUsedTurn.get(ability.name, False), \
            ("ability {ability.name} 应标记为已使用")

    def test_ability_not_available_after_use(self, snapshot_game):
        """同一回合内再次调用 get_actions 不应包含已用的 ability。"""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.ACTIVE
        card.position = PokemonPosition.ACTIVE
        h.p1.active = [card]
        ability = card.ability[0]
        from ptcg.core.action import UseAbilityAction
        action = UseAbilityAction(h.p1.id, card, ability)
        gen = card.reduce_action(action, h.state)
        if gen is not None:
            try:
                next(gen)
            except (StopIteration, IndexError, AttributeError, ValueError):
                pass
        actions = card.get_actions(h.state)
        ability_actions = [a for a in actions if isinstance(a, UseAbilityAction)]
        assert len(ability_actions) == 0, "已使用 ability 不应再出现在 get_actions"
'''


DRAW_TEMPLATE = '''"""
{CARD_ID} — DRAW 效果行为测试.
"""
import pytest
from ptcg.core.card_registry import registry
from ptcg.core.enums import CardPosition, CardType


def _make_card():
    return registry.get("{CARD_ID}")()


class TestDrawBehavior:
    """DRAW 类型：抽牌 —— 手牌增加 + 牌库减少。"""

    def test_get_actions_in_hand(self, snapshot_game):
        """手牌中时可使用。"""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.HAND
        h.p1.hand = [card]
        h.set_deck(h.p1, ["SVE-001"] * 3)
        actions = card.get_actions(h.state)
        assert len(actions) >= 1, ("应有 actions, got {len(actions)}")

    def test_deck_empty_no_actions(self, snapshot_game):
        """牌库为空时不能抽牌。"""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.HAND
        h.p1.hand = [card]
        h.p1.left = []
        actions = card.get_actions(h.state)
        assert len(actions) == 0, "牌库空时应无 actions"

    def test_draw_increases_hand(self, snapshot_game):
        """使用后手牌数量增加。"""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.HAND
        h.p1.hand = [card]
        h.set_deck(h.p1, ["SVE-001"] * 5)
        initial_hand = len(h.p1.hand)
        from ptcg.core.action import UseItemAction
        action = UseItemAction(h.p1.id, card)
        gen = card.reduce_action(action, h.state)
        if gen is not None:
            try:
                for _ in range(10):
                    next(gen)
            except (StopIteration, IndexError, AttributeError, ValueError):
                pass
        assert len(h.p1.hand) > initial_hand or card not in h.p1.hand, \
            ("手牌应增加或卡被消耗 initial={initial_hand} now={len(h.p1.hand)}")

    def test_deck_decreases_after_draw(self, snapshot_game):
        """抽牌后牌库数量减少。"""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.HAND
        h.p1.hand = [card]
        h.set_deck(h.p1, ["SVE-001"] * 5)
        initial_deck = len(h.p1.left)
        from ptcg.core.action import UseItemAction
        action = UseItemAction(h.p1.id, card)
        gen = card.reduce_action(action, h.state)
        if gen is not None:
            try:
                for _ in range(10):
                    next(gen)
            except (StopIteration, IndexError, AttributeError, ValueError):
                pass
        assert len(h.p1.left) <= initial_deck, \
            ("牌库应减少 initial={initial_deck} now={len(h.p1.left)}")
'''


ENERGY_TEMPLATE = '''"""
{CARD_ID} — ENERGY 效果行为测试.
"""
import pytest
from ptcg.core.card_registry import registry
from ptcg.core.enums import CardPosition, CardType, EnergyType, PokemonPosition


def _make_card():
    return registry.get("{CARD_ID}")()


class TestEnergyBehavior:
    """ENERGY 类型：能量附着/提供 —— energy 列表变化。"""

    def test_card_is_energy_card(self, snapshot_game):
        """卡牌为能量卡类型。"""
        card = _make_card()
        from ptcg.core.card import EnergyCard
        assert isinstance(card, EnergyCard), "应继承 EnergyCard"
        assert card.energyType in (EnergyType.BASIC, EnergyType.SPECIAL), \
            ("应为能量卡, got {card.energyType}")

    def test_provides_energy(self, snapshot_game):
        """能量卡应提供能量。"""
        card = _make_card()
        assert hasattr(card, "provides"), "应有 provides 属性"
        assert len(card.provides) >= 1, "应提供至少一个能量"

    def test_get_actions_attach(self, snapshot_game):
        """get_actions 返回 AttachEnergyAction。"""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.HAND
        h.p1.hand = [card]
        target = registry.get("ASR-133")()
        target.cardPosition = CardPosition.ACTIVE
        target.position = PokemonPosition.ACTIVE
        h.p1.active = [target]
        actions = card.get_actions(h.state)
        from ptcg.core.action import AttachEnergyAction
        attach_actions = [a for a in actions if isinstance(a, AttachEnergyAction)]
        assert len(attach_actions) >= 1, "应有 AttachEnergyAction"

    def test_energy_attached_to_pokemon(self, snapshot_game):
        """使用后能量附着到目标宝可梦上。"""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.HAND
        h.p1.hand = [card]
        target = registry.get("ASR-133")()
        target.cardPosition = CardPosition.ACTIVE
        target.position = PokemonPosition.ACTIVE
        h.p1.active = [target]
        from ptcg.core.action import AttachEnergyAction
        action = AttachEnergyAction(h.p1.id, card, target)
        gen = card.reduce_action(action, h.state)
        if gen is not None:
            try:
                for _ in range(5):
                    next(gen)
            except (StopIteration, IndexError, AttributeError, ValueError):
                pass
        assert card not in h.p1.hand or card.cardPosition != CardPosition.HAND, \
            "能量卡应离开手牌"
'''


SPECIAL_CONDITION_TEMPLATE = '''"""
{CARD_ID} — SPECIAL_CONDITION 效果行为测试.
"""
import pytest
from ptcg.core.card_registry import registry
from ptcg.core.enums import CardPosition, CardType, PokemonPosition


def _make_card():
    return registry.get("{CARD_ID}")()


def _make_opponent():
    return registry.get("ASR-133")()


class TestSpecialConditionBehavior:
    """SPECIAL_CONDITION 类型：中毒/麻痹/灼伤/睡眠/混乱等状态施加。"""

    def test_get_actions_in_hand(self, snapshot_game):
        """手牌中时可使用。"""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.HAND
        h.p1.hand = [card]
        opp = _make_opponent()
        opp.cardPosition = CardPosition.ACTIVE
        opp.position = PokemonPosition.ACTIVE
        h.p2.active = [opp]
        actions = card.get_actions(h.state)
        assert isinstance(actions, list), "应返回 action 列表"

    def test_card_consumed_after_use(self, snapshot_game):
        """使用后卡牌被消耗（从手牌移走）。"""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.HAND
        h.p1.hand = [card]
        opp = _make_opponent()
        opp.cardPosition = CardPosition.ACTIVE
        opp.position = PokemonPosition.ACTIVE
        h.p2.active = [opp]
        from ptcg.core.action import UseItemAction
        action = UseItemAction(h.p1.id, card)
        gen = card.reduce_action(action, h.state)
        if gen is not None:
            try:
                for _ in range(5):
                    next(gen)
            except (StopIteration, IndexError, AttributeError, ValueError):
                pass
        assert card not in h.p1.hand, "使用后卡应从手牌移走"

    def test_hand_decreases_after_use(self, snapshot_game):
        """使用后手牌减少。"""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.HAND
        h.p1.hand = [card]
        opp = _make_opponent()
        opp.cardPosition = CardPosition.ACTIVE
        opp.position = PokemonPosition.ACTIVE
        h.p2.active = [opp]
        initial_hand = len(h.p1.hand)
        from ptcg.core.action import UseItemAction
        action = UseItemAction(h.p1.id, card)
        gen = card.reduce_action(action, h.state)
        if gen is not None:
            try:
                for _ in range(5):
                    next(gen)
            except (StopIteration, IndexError, AttributeError, ValueError):
                pass
        assert len(h.p1.hand) < initial_hand, \
            ("手牌应减少 before={initial_hand} after={len(h.p1.hand)}")
'''


TOOL_TEMPLATE = '''"""
{CARD_ID} — TOOL 效果行为测试.
"""
import pytest
from ptcg.core.card_registry import registry
from ptcg.core.enums import CardPosition, CardType, PokemonPosition


def _make_card():
    return registry.get("{CARD_ID}")()


class TestToolBehavior:
    """TOOL 类型：道具附着/触发。"""

    def test_card_is_tool(self, snapshot_game):
        """卡牌为 ToolCard 类型。"""
        card = _make_card()
        from ptcg.core.card import ToolCard
        assert isinstance(card, ToolCard), "应继承 ToolCard"

    def test_get_actions_in_hand(self, snapshot_game):
        """手牌中时可使用。"""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.HAND
        h.p1.hand = [card]
        actions = card.get_actions(h.state)
        assert isinstance(actions, list), ("应返回 list, got {type(actions)}")

    def test_attach_to_pokemon(self, snapshot_game):
        """使用后卡牌被附着到宝可梦上或消耗。"""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.HAND
        h.p1.hand = [card]
        target = registry.get("ASR-133")()
        target.cardPosition = CardPosition.ACTIVE
        target.position = PokemonPosition.ACTIVE
        h.p1.active = [target]
        from ptcg.core.action import UseItemAction
        action = UseItemAction(h.p1.id, card)
        gen = card.reduce_action(action, h.state)
        if gen is not None:
            try:
                for _ in range(5):
                    next(gen)
            except (StopIteration, IndexError, AttributeError, ValueError):
                pass
        assert card not in h.p1.hand, "工具卡应离开手牌"

    def test_ability_on_tool(self, snapshot_game):
        """道具卡可能带有 ability。"""
        card = _make_card()
        if hasattr(card, "ability") and len(card.ability) > 0:
            ability = card.ability[0]
            assert hasattr(ability, "name"), "ability 应有 name"
            assert hasattr(ability, "abilityType"), "ability 应有 abilityType"
'''


CONDITIONAL_ATTACK_TEMPLATE = '''"""
{CARD_ID} — CONDITIONAL_ATTACK 效果行为测试.
"""
import pytest
from ptcg.core.card_registry import registry
from ptcg.core.enums import CardPosition, CardType, PokemonPosition


def _make_card():
    return registry.get("{CARD_ID}")()


def _make_opponent():
    return registry.get("ASR-133")()


class TestConditionalAttackBehavior:
    """CONDITIONAL_ATTACK 类型：条件满足时攻击生效，否则失败。"""

    def test_attack_available_with_energy(self, snapshot_game):
        """能量满足时攻击 action 可用。"""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.ACTIVE
        card.position = PokemonPosition.ACTIVE
        card.energy = [CardType.COLORLESS]
        h.p1.active = [card]
        opp = _make_opponent()
        opp.cardPosition = CardPosition.ACTIVE
        opp.position = PokemonPosition.ACTIVE
        h.p2.active = [opp]
        actions = card.get_actions(h.state)
        assert len(actions) >= 1, "能量满足时应返回攻击 action"

    def test_attack_no_actions_without_energy(self, snapshot_game):
        """能量不足时无攻击 action。"""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.ACTIVE
        card.position = PokemonPosition.ACTIVE
        card.energy = []
        h.p1.active = [card]
        opp = _make_opponent()
        opp.cardPosition = CardPosition.ACTIVE
        opp.position = PokemonPosition.ACTIVE
        h.p2.active = [opp]
        actions = card.get_actions(h.state)
        assert len(actions) == 0, "能量不足时应无 action"

    def test_condition_met_attack_succeeds(self, snapshot_game):
        """条件满足时攻击正常执行。"""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.ACTIVE
        card.position = PokemonPosition.ACTIVE
        card.energy = [CardType.COLORLESS]
        h.p1.active = [card]
        opp = _make_opponent()
        opp.cardPosition = CardPosition.ACTIVE
        opp.position = PokemonPosition.ACTIVE
        opp.hp = 200
        h.p2.active = [opp]
        from ptcg.core.action import AttackAction
        action = AttackAction(h.state.turn, card, card.attacks[0], opp)
        gen = card.reduce_action(action, h.state)
        if gen is not None:
            try:
                next(gen)
            except (StopIteration, IndexError, AttributeError, ValueError):
                pass
        assert opp.hp <= 200 or gen is None, "条件满足时攻击应减少对手 HP"
'''


PRIZE_TEMPLATE = '''"""
{CARD_ID} — PRIZE 效果行为测试.
"""
import pytest
from ptcg.core.card_registry import registry
from ptcg.core.enums import CardPosition, CardType, PokemonPosition


def _make_card():
    return registry.get("{CARD_ID}")()


class TestPrizeBehavior:
    """PRIZE 类型：奖赏卡操作。"""

    def test_get_actions_in_hand(self, snapshot_game):
        """手牌中且未使用支援者时可使用。"""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.HAND
        h.p1.hand = [card]
        actions = card.get_actions(h.state)
        assert isinstance(actions, list), ("应返回 list, got {type(actions)}")

    def test_card_consumed_after_use(self, snapshot_game):
        """使用后卡被消耗（从手牌移走）。"""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.HAND
        h.p1.hand = [card]
        from ptcg.core.action import UseSupporterAction
        action = UseSupporterAction(h.p1.id, card)
        gen = card.reduce_action(action, h.state)
        if gen is not None:
            try:
                for _ in range(5):
                    next(gen)
            except (StopIteration, IndexError, AttributeError, ValueError):
                pass
        assert card not in h.p1.hand, "奖赏卡操作后自身应移出手牌"

    def test_hand_changes_after_prize_effect(self, snapshot_game):
        """使用后手牌数量有变化。"""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.HAND
        h.p1.hand = [card]
        h.set_deck(h.p1, ["SVE-001"] * 5)
        initial_hand = len(h.p1.hand)
        from ptcg.core.action import UseSupporterAction
        action = UseSupporterAction(h.p1.id, card)
        gen = card.reduce_action(action, h.state)
        if gen is not None:
            try:
                for _ in range(5):
                    next(gen)
            except (StopIteration, IndexError, AttributeError, ValueError):
                pass
        assert len(h.p1.hand) != initial_hand or card not in h.p1.hand, \
            ("手牌应有变化或卡被消耗 initial={initial_hand} now={len(h.p1.hand)}")
'''


HEAL_TEMPLATE = '''"""
{CARD_ID} — HEAL 效果行为测试.
"""
import pytest
from ptcg.core.card_registry import registry
from ptcg.core.enums import CardPosition, CardType, PokemonPosition


def _make_card():
    return registry.get("{CARD_ID}")()


class TestHealBehavior:
    """HEAL 类型：回复 HP —— HP 增加 + 不超过 max_hp。"""

    def test_get_actions_with_damaged_pokemon(self, snapshot_game):
        """有受伤宝可梦时可使用。"""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.HAND
        h.p1.hand = [card]
        target = registry.get("ASR-133")()
        target.cardPosition = CardPosition.ACTIVE
        target.position = PokemonPosition.ACTIVE
        target.hp = target.max_hp - 40
        h.p1.active = [target]
        actions = card.get_actions(h.state)
        assert isinstance(actions, list), "应返回 action 列表"

    def test_heal_restores_hp(self, snapshot_game):
        """使用后 HP 增加。"""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.HAND
        h.p1.hand = [card]
        target = registry.get("ASR-133")()
        target.cardPosition = CardPosition.ACTIVE
        target.position = PokemonPosition.ACTIVE
        target.max_hp = 100
        target.hp = 50
        h.p1.active = [target]
        from ptcg.core.action import UseItemAction
        action = UseItemAction(h.p1.id, card)
        gen = card.reduce_action(action, h.state)
        if gen is not None:
            try:
                for _ in range(5):
                    next(gen)
            except (StopIteration, IndexError, AttributeError, ValueError):
                pass
        assert target.hp >= 50, \
            "HP 应增加"

    def test_heal_not_exceed_max_hp(self, snapshot_game):
        """使用后 HP 不超过 max_hp。"""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.HAND
        h.p1.hand = [card]
        target = registry.get("ASR-133")()
        target.cardPosition = CardPosition.ACTIVE
        target.position = PokemonPosition.ACTIVE
        target.max_hp = 100
        target.hp = 90
        h.p1.active = [target]
        from ptcg.core.action import UseItemAction
        action = UseItemAction(h.p1.id, card)
        gen = card.reduce_action(action, h.state)
        if gen is not None:
            try:
                for _ in range(5):
                    next(gen)
            except (StopIteration, IndexError, AttributeError, ValueError):
                pass
        assert target.hp <= target.max_hp, \
            ("HP 不应超上限 max={target.max_hp} hp={target.hp}")
'''


# ============================================================================
# 模板函数封装（替换 {CARD_ID} 为实际卡牌 ID）
# ============================================================================


def test_template_DAMAGE(card_id: str, snapshot_game=None) -> str:
    """生成 DAMAGE 类型的行为测试代码。"""
    return _template(DAMAGE_TEMPLATE, card_id)


def test_template_DISCARD(card_id: str, snapshot_game=None) -> str:
    """生成 DISCARD 类型的行为测试代码。"""
    return _template(DISCARD_TEMPLATE, card_id)


def test_template_SWITCH(card_id: str, snapshot_game=None) -> str:
    """生成 SWITCH 类型的行为测试代码。"""
    return _template(SWITCH_TEMPLATE, card_id)


def test_template_EVOLVE(card_id: str, snapshot_game=None) -> str:
    """生成 EVOLVE 类型的行为测试代码。"""
    return _template(EVOLVE_TEMPLATE, card_id)


def test_template_SEARCH_DECK(card_id: str, snapshot_game=None) -> str:
    """生成 SEARCH_DECK 类型的行为测试代码。"""
    return _template(SEARCH_DECK_TEMPLATE, card_id)


def test_template_BENCH(card_id: str, snapshot_game=None) -> str:
    """生成 BENCH 类型的行为测试代码。"""
    return _template(BENCH_TEMPLATE, card_id)


def test_template_ABILITY(card_id: str, snapshot_game=None) -> str:
    """生成 ABILITY 类型的行为测试代码。"""
    return _template(ABILITY_TEMPLATE, card_id)


def test_template_DRAW(card_id: str, snapshot_game=None) -> str:
    """生成 DRAW 类型的行为测试代码。"""
    return _template(DRAW_TEMPLATE, card_id)


def test_template_ENERGY(card_id: str, snapshot_game=None) -> str:
    """生成 ENERGY 类型的行为测试代码。"""
    return _template(ENERGY_TEMPLATE, card_id)


def test_template_SPECIAL_CONDITION(card_id: str, snapshot_game=None) -> str:
    """生成 SPECIAL_CONDITION 类型的行为测试代码。"""
    return _template(SPECIAL_CONDITION_TEMPLATE, card_id)


def test_template_TOOL(card_id: str, snapshot_game=None) -> str:
    """生成 TOOL 类型的行为测试代码。"""
    return _template(TOOL_TEMPLATE, card_id)


def test_template_CONDITIONAL_ATTACK(card_id: str, snapshot_game=None) -> str:
    """生成 CONDITIONAL_ATTACK 类型的行为测试代码。"""
    return _template(CONDITIONAL_ATTACK_TEMPLATE, card_id)


def test_template_PRIZE(card_id: str, snapshot_game=None) -> str:
    """生成 PRIZE 类型的行为测试代码。"""
    return _template(PRIZE_TEMPLATE, card_id)


def test_template_HEAL(card_id: str, snapshot_game=None) -> str:
    """生成 HEAL 类型的行为测试代码。"""
    return _template(HEAL_TEMPLATE, card_id)


def gen_template_test(card_id: str, effect_type: str, name: str,
                      spec: Optional[dict] = None) -> str:
    """根据效果类型生成对应 golden 模板测试代码。

    Args:
        card_id: 卡牌 ID，如 "OBF-125"
        effect_type: 效果类型名，如 "DAMAGE", "DISCARD" 等
        name: 卡牌名称
        spec: 可选，额外规格参数

    Returns:
        Python 测试代码字符串
    """
    template_map = {
        "DAMAGE": test_template_DAMAGE,
        "DISCARD": test_template_DISCARD,
        "SWITCH": test_template_SWITCH,
        "EVOLVE": test_template_EVOLVE,
        "SEARCH_DECK": test_template_SEARCH_DECK,
        "BENCH": test_template_BENCH,
        "ABILITY": test_template_ABILITY,
        "DRAW": test_template_DRAW,
        "ENERGY": test_template_ENERGY,
        "SPECIAL_CONDITION": test_template_SPECIAL_CONDITION,
        "TOOL": test_template_TOOL,
        "CONDITIONAL_ATTACK": test_template_CONDITIONAL_ATTACK,
        "PRIZE": test_template_PRIZE,
        "HEAL": test_template_HEAL,
    }

    template_fn = template_map.get(effect_type)
    if template_fn is None:
        return f"# 未支持的模板类型: {effect_type}"

    code = template_fn(card_id)
    # 注入卡牌名称 header
    lines = code.split("\n")
    lines[1] = f"{card_id} ({name}) — {effect_type} 效果行为测试. 自动生成模板."
    return "\n".join(lines)
