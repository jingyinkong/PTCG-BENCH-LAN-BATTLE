"""Terapagos ex - SCR 128"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import (
    reduce_attack_action, reduce_evolve_pokemon_action,
    reduce_play_pokemon_action, reduce_retreat_action
)
from ptcg.utils.utils import (
    auto_end_turn, check_energy, current_player, opponent_active
)


class SCR128Terapagosex(PokemonCard):
    """Terapagos ex - BASIC Pokemon. HP: 230. Tera.

    Attacks:
    - Allied Strike: 30× bench count damage. Cannot use on first turn if
      going second. (First-turn restriction not enforced in engine.)
    - Crown Opal: 180 damage. Immune to Basic non-Colorless attacks next
      opponent turn. (Protection flag set but not enforced by engine.)
    """
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "SCR"
        self.number = "128"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "太乐巴戈斯ex"
        self.hp = 230
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.TERA
        self.stage = Stage.BASIC
        self.cardType = CardType.COLORLESS
        self.retreat = [CardType.COLORLESS] * 2
        self.weakness = [CardType.FIGHTING]
        self.resistance = []
        self.evolveFrom = []
        self.prize = 2
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.attacks = [
            Attack({
                "name": "同盟打击",
                "damage": 30,
                "cost": [CardType.COLORLESS, CardType.COLORLESS],
                "text": "这个招式，在后攻玩家的最初回合无法使用。造成自己备战宝可梦数量x30伤害。"
            }),
            Attack({
                "name": "皇冠蛋白石",
                "damage": 180,
                "cost": [CardType.GRASS, CardType.WATER, CardType.LIGHTNING],
                "text": "在下一个对手的回合，这只宝可梦不会受到【基础】宝可梦（除【无】宝可梦外）的招式的伤害。"
            })
        ]

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
        elif isinstance(action, RetreatAction):
            reduce_retreat_action(action, state)
        elif isinstance(action, AttackAction):
            if action.attack == self.attacks[0]:
                # 同盟打击: 备战数量 × 30
                player = current_player(state)
                bench_count = len(player.bench)
                action.attack.damage = 30 * bench_count
            yield from reduce_attack_action(action, state)