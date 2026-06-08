"""Scream Tail - PRE 042"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import auto_end_turn, check_energy, current_player, opponent_active


class PRE042ScreamTail(PokemonCard):
    """Scream Tail - BASIC Pokemon. HP: 90.
    Attack: Roaring Scream - Damage = damage counters on this Pokemon x 20."""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "PRE"; self.number = "042"; self.id = f"{self.set_name}-{self.number}"
        self.name = "吼叫尾"; self.hp = 90
        self.pokemonType = PokemonType.NORMAL; self.pokemonRule = PokemonRule.NONE; self.stage = Stage.BASIC
        self.cardType = CardType.PSYCHIC
        self.retreat = [CardType.COLORLESS]; self.weakness = [CardType.DARK]; self.resistance = [CardType.FIGHTING]
        self.evolveFrom = []; self.prize = 1
        self.energy = []; self.attachment = []; self.evolved = []
        self.attacks = [
            Attack({"name": "巴掌","damage": 30,"cost": [CardType.PSYCHIC],"text": ""}),
            Attack({"name": "凶暴吼叫","damage": 0,"cost": [CardType.PSYCHIC,CardType.COLORLESS],"text": "给对手的1只宝可梦，造成这只宝可梦身上放置的伤害指示物数量x20伤害。"})
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
        if isinstance(action, PlayPokemonAction): reduce_play_pokemon_action(action, state)
        elif isinstance(action, EvolvePokemonAction): reduce_evolve_pokemon_action(action, state)
        elif isinstance(action, RetreatAction): yield from reduce_retreat_action(action, state)
        elif isinstance(action, AttackAction):
            if action.attack.name == "凶暴吼叫":
                # 伤害 = 自身伤害指示物数量 x 20
                damage_counters = (self.max_hp if hasattr(self,'max_hp') else 90) - self.hp
                action.attack.damage = max(0, damage_counters) * 2  # 10HP per counter, x20 = x2 in tens
                yield from reduce_attack_action(action, state)
            else:
                yield from reduce_attack_action(action, state)
