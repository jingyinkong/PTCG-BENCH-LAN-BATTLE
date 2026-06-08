"""Archaludon ex - SSP 130"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, opponent_active


class SSP130Archaludonex(PokemonCard):
    """Archaludon ex - STAGE_1 Pokemon. HP: 300."""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "SSP"
        self.number = "130"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "铝钢桥龙ex"
        self.hp = 300
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.STAGE_1
        self.cardType = CardType.METAL
        self.retreat = [CardType.COLORLESS] * 2
        self.weakness = [CardType.FIRE]
        self.resistance = [CardType.GRASS]
        self.evolveFrom = ['铝钢龙']
        self.prize = 2
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.attacks = [
        Attack({"name": "金属防卫", "damage": 220, "cost": [CardType.METAL, CardType.METAL, CardType.METAL], "text": "在下一个对手的回合，这只宝可梦的弱点，全部消除。"})
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
