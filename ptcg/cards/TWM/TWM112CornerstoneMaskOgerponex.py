"""厄诡椪 础石面具ex - TWM 112"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, opponent_active


class TWM112CornerstoneMaskOgerponex(PokemonCard):
    """厄诡椪 础石面具ex - BASIC 宝可梦。HP: 210。"""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "TWM"
        self.number = "112"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "厄诡椪 础石面具ex"
        self.hp = 210
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.FIGHTING
        self.retreat = [CardType.COLORLESS] * 1
        self.weakness = [CardType.GRASS]
        self.resistance = []
        self.evolveFrom = []
        self.prize = 2
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.attacks = [
        Attack({"name": "打爆", "damage": 140, "cost": [CardType.FIGHTING, CardType.COLORLESS, CardType.COLORLESS], "text": "这个招式的伤害，不计算弱点、抗性以及对手战斗宝可梦身上所附加的效果。"})
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
