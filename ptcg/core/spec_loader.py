"""SpecBasedCard — 从 JSON CardSpec 动态生成卡牌实例。

动态创建 Card 子类以绕过抽象方法限制。
"""
from __future__ import annotations

from ptcg.core.ability import ActiveAbility
from ptcg.core.attack import Attack
from ptcg.core.card import (EnergyCard, ItemCard, PokemonCard,
                             SupporterCard, StadiumCard, ToolCard, Card)
from ptcg.core.card_spec_schema import CardSpec
from ptcg.core.enums import (AbilityType, CardType, PokemonType)

_CT = {
    "COLORLESS": CardType.COLORLESS, "FIRE": CardType.FIRE, "WATER": CardType.WATER,
    "LIGHTNING": CardType.LIGHTNING, "GRASS": CardType.GRASS, "PSYCHIC": CardType.PSYCHIC,
    "FIGHTING": CardType.FIGHTING, "DARK": CardType.DARK, "METAL": CardType.METAL,
    "DRAGON": CardType.DRAGON, "FAIRY": CardType.FAIRY, "NONE": CardType.NONE,
}
_PT = {"BASIC": PokemonType.V, "EX_LOWERCASE": PokemonType.EX_LOWERCASE,
       "V": PokemonType.V, "VSTAR": PokemonType.VSTAR, "RADIANT": PokemonType.RADIANT}

_BASE = {
    "POKEMON": PokemonCard, "ENERGY": EnergyCard,
    "ITEM": ItemCard, "SUPPORTER": SupporterCard,
    "STADIUM": StadiumCard, "TOOL": ToolCard,
}


def _ct(s: str) -> CardType:
    return _CT.get(s, CardType.COLORLESS)


def _make_get_actions(spec: CardSpec):
    """生成 get_actions 方法（闭包）。"""
    def get_actions(self, state):
        from ptcg.core.action import UseItemAction, UseSupporterAction
        from ptcg.utils.utils import current_player
        from ptcg.core.enums import PokemonPosition

        player = current_player(state)
        actions = []

        # Check conditions
        cond_ok = True
        for c in spec.conditions:
            from ptcg.core.effect_primitives import check_condition
            if not check_condition(c, state, player):
                cond_ok = False
                break

        if not cond_ok:
            return actions

        # Pokemon: attack actions
        if spec.super_type == "POKEMON" and self.position == PokemonPosition.ACTIVE:
            from ptcg.utils.utils import opponent_active, check_energy
            targets = opponent_active(state)
            for atk in self.attacks:
                if check_energy(atk.cost, self.energy):
                    from ptcg.core.action import AttackAction
                    actions.extend(AttackAction(state.turn, self, atk, t) for t in targets)

        # Trainer: use action
        if spec.trainer_type == "ITEM":
            if self in player.hand:
                actions.append(UseItemAction(state.turn, self))
        elif spec.trainer_type == "SUPPORTER":
            if self in player.hand and not player.supporterPlayedTurn:
                actions.append(UseSupporterAction(state.turn, self))

        return actions
    return get_actions


def _make_reduce_action(spec: CardSpec):
    """生成 reduce_action 方法（闭包）。"""
    def reduce_action(self, action, state):
        from ptcg.core.action import (UseItemAction, UseSupporterAction,
                                       AttackAction, PlayPokemonAction)
        from ptcg.utils.utils import current_player

        player = current_player(state)

        if isinstance(action, PlayPokemonAction):
            from ptcg.core.reducer import reduce_play_pokemon_action
            reduce_play_pokemon_action(action, state)

        elif isinstance(action, (UseItemAction, UseSupporterAction)):
            # Execute primitive sequence from spec
            for step in spec.effects:
                for pc in step.primitives:
                    self._exec_primitive(pc, state, player)
            # Mark supporter played
            if isinstance(action, UseSupporterAction):
                player.supporterPlayedTurn = True

        elif isinstance(action, AttackAction):
            from ptcg.core.reducer import reduce_attack_action
            yield from reduce_attack_action(action, state)

    return reduce_action


def _exec_primitive(self, pc, state, player):
    """执行单个原语调用（实例方法，注入到动态类）。"""
    from ptcg.core.effect_primitives import PRIMITIVE_REGISTRY, use_and_discard_self
    fn = PRIMITIVE_REGISTRY.get(pc.op)
    if fn is None:
        return

    params = dict(pc.params)
    # Inject common context
    if 'state' in fn.__code__.co_varnames[:len(params) + 3]:
        params.setdefault('state', state)
    if 'player' in fn.__code__.co_varnames[:len(params) + 3]:
        params.setdefault('player', player)

    # Special handling for use_and_discard_self
    if pc.op == "use_and_discard_self":
        use_and_discard_self(self, player, state)
        return

    # Handle generator primitives (those with yield)
    try:
        result = fn(**params)
        if hasattr(result, '__next__'):
            # generator — drain it
            try:
                while True:
                    next(result)
            except StopIteration:
                pass
    except Exception:
        pass  # best-effort for now


def build_card_from_spec(spec: CardSpec) -> Card:
    """从 CardSpec 动态构建卡牌实例。"""
    tt = spec.trainer_type or ""
    key = tt if spec.super_type == "TRAINER" and tt in _BASE else spec.super_type
    base_cls = _BASE.get(key, Card)

    # Create dynamic subclass with get_actions + reduce_action
    dyn_cls = type(
        f"Spec_{spec.card_id.replace('-','_')}",
        (base_cls,),
        {
            "get_actions": _make_get_actions(spec),
            "reduce_action": _make_reduce_action(spec),
            "_exec_primitive": _exec_primitive,
        }
    )

    card = dyn_cls()
    # Common
    card.id = spec.card_id
    card.name = spec.name
    card.set_name = spec.set_name
    card.number = spec.number

    # Pokemon
    if isinstance(card, PokemonCard) and spec.hp:
        card.hp = spec.hp
        card.pokemonType = _PT.get(spec.pokemon_type, PokemonType.V)
        card.cardType = _ct(spec.card_type)
        card.retreat = [_ct(r) for r in spec.retreat]
        card.weakness = [_ct(w) for w in spec.weakness]
        card.resistance = [_ct(r) for r in spec.resistance]
        card.prize = spec.prize
        card.energy = []
        card.attachment = []
        card.attacks = [Attack({"name": a.name, "damage": a.damage,
                                "cost": [_ct(c) for c in a.cost], "text": a.text})
                        for a in spec.attacks]
        card.ability = [ActiveAbility({"name": a.name, "abilityType": AbilityType.ACTIVE_ABILITY,
                                       "text": a.text}) for a in spec.abilities]

    # Energy
    if isinstance(card, EnergyCard):
        card.provides = [_ct(p) for p in spec.provides]

    # Effect text
    if spec.effect_text and hasattr(card, "text"):
        card.text = spec.effect_text

    return card


def load_specs_from_dir(path: str) -> list[Card]:
    import json
    from pathlib import Path
    cards = []
    for f in sorted(Path(path).glob("*.json")):
        spec = CardSpec.model_validate(json.loads(f.read_text(encoding="utf-8")))
        cards.append(build_card_from_spec(spec))
    return cards
