"""奇诺栗鼠 - TEF 137"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import AbilityType, CardPosition, CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, opponent_active


class TEF137Cinccino(PokemonCard):
    """奇诺栗鼠 - STAGE_1 宝可梦。HP: 110。"""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "TEF"
        self.number = "137"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "奇诺栗鼠"
        self.hp = 110
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.STAGE_1
        self.cardType = CardType.COLORLESS
        self.retreat = [CardType.COLORLESS] * 1
        self.weakness = [CardType.FIGHTING]
        self.resistance = []
        self.evolveFrom = ['泡沫栗鼠']
        self.prize = 1
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.attacks = [
        Attack({"name": "重掴", "damage": 30, "cost": [CardType.COLORLESS], "text": ""}),
        Attack({"name": "特殊滚动", "damage": 70, "cost": [CardType.COLORLESS, CardType.COLORLESS], "text": "造成这只宝可梦身上附着的特殊能量张数×70伤害。"})
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

