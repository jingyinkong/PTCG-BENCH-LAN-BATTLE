"""Dusknoir - SFA 020"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, opponent_active


class SFA020Dusknoir(PokemonCard):
    """Dusknoir - STAGE_2 Pokemon. HP: 160."""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "SFA"
        self.number = "020"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "黑夜魔灵"
        self.hp = 160
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.STAGE_2
        self.cardType = CardType.PSYCHIC
        self.retreat = [CardType.COLORLESS] * 3
        self.weakness = [CardType.DARK]
        self.resistance = [CardType.FIGHTING]
        self.evolveFrom = ['彷徨夜灵']
        self.prize = 1
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.attacks = [
        Attack({"name": "影子束缚", "damage": 150, "cost": [CardType.PSYCHIC, CardType.PSYCHIC, CardType.COLORLESS], "text": "在下一个对手的回合，受到这个招式影响的宝可梦，无法撤退。"})
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
