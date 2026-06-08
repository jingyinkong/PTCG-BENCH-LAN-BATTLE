"""Scizor - OBF 205"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, opponent_active


class OBF205Scizor(PokemonCard):
    """Scizor - STAGE_1 Pokemon. HP: 140."""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "OBF"
        self.number = "205"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "巨钳螳螂"
        self.hp = 140
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.STAGE_1
        self.cardType = CardType.METAL
        self.retreat = [CardType.COLORLESS] * 2
        self.weakness = [CardType.FIRE]
        self.resistance = [CardType.GRASS]
        self.evolveFrom = ['飞天螳螂']
        self.prize = 1
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.attacks = [
        Attack({"name": "惩罚巨钳", "damage": 10, "cost": [CardType.METAL], "text": "追加造成对手场上拥有特性的宝可梦数量x50伤害。"}),
        Attack({"name": "居合劈", "damage": 70, "cost": [CardType.METAL, CardType.METAL], "text": ""})
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
