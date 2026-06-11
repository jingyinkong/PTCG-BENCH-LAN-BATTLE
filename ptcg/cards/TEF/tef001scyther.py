"""飞天螳螂 - TEF 001"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import AbilityType, CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, opponent_active


class TEF001Scyther(PokemonCard):
    """飞天螳螂 - BASIC 宝可梦。HP: 90。"""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "TEF"
        self.number = "001"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "飞天螳螂"
        self.hp = 90
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.GRASS
        self.retreat = [CardType.COLORLESS] * 1
        self.weakness = [CardType.FIRE]
        self.resistance = []
        self.evolveFrom = []
        self.prize = 1
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.attacks = [
        Attack({"name": "切开", "damage": 10, "cost": [CardType.COLORLESS], "text": ""}),
        Attack({"name": "斩落", "damage": 60, "cost": [CardType.COLORLESS, CardType.COLORLESS], "text": "在下一个自己的回合，这只宝可梦无法使用「斩落」。"})
        ]
        self.ability = []

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

