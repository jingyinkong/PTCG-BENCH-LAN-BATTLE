"""Duraludon - SSP 129"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, opponent_active


class SSP129Duraludon(PokemonCard):
    """Duraludon - BASIC Pokemon. HP: 130."""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "SSP"
        self.number = "129"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "铝钢龙"
        self.hp = 130
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.METAL
        self.retreat = [CardType.COLORLESS] * 2
        self.weakness = [CardType.FIRE]
        self.resistance = [CardType.GRASS]
        self.evolveFrom = []
        self.prize = 1
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.attacks = [
        Attack({"name": "正面对决", "damage": 50, "cost": [CardType.METAL, CardType.METAL], "text": ""}),
        Attack({"name": "铝钢光束", "damage": 130, "cost": [CardType.METAL, CardType.METAL, CardType.METAL], "text": "选择这只宝可梦身上附着的2个能量，放于弃牌区。"})
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
