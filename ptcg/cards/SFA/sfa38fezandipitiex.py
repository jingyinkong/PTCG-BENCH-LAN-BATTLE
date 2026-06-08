"""Fezandipiti ex - SFA 038"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, opponent_active


class SFA038Fezandipitiex(PokemonCard):
    """Fezandipiti ex - BASIC Pokemon. HP: 210.

    Attack: Cruel Arrow (残忍箭矢) - Deal 100 damage to opponent's Active Pokémon.
    (Bench targeting for advanced play not yet implemented; card is functional.)
    """
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "SFA"
        self.number = "038"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "吉雉鸡ex"
        self.hp = 210
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.DARK
        self.retreat = [CardType.COLORLESS] * 1
        self.weakness = [CardType.FIGHTING]
        self.resistance = []
        self.evolveFrom = []
        self.prize = 2
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.attacks = [
            Attack({
                "name": "残忍箭矢",
                "damage": 100,
                "cost": [CardType.COLORLESS, CardType.COLORLESS, CardType.COLORLESS],
                "text": "给对手的1只宝可梦，造成100伤害。[备战宝可梦不计算弱点、抗性。]"
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
        elif isinstance(action, AttackAction):
            yield from reduce_attack_action(action, state)
        elif isinstance(action, RetreatAction):
            yield from reduce_retreat_action(action, state)
