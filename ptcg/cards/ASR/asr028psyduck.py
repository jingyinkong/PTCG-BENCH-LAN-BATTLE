"""可达鸭 - ASR 028"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import AbilityType, CardPosition, CardType, Coin, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, current_player, flip_coin, opponent_active


class ASR028Psyduck(PokemonCard):
    """可达鸭 - BASIC 宝可梦。HP: 60。"""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "ASR"
        self.number = "028"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "可达鸭"
        self.hp = 60
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.WATER
        self.retreat = [CardType.COLORLESS] * 1
        self.weakness = [CardType.LIGHTNING]
        self.resistance = []
        self.evolveFrom = []
        self.prize = 1
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.attacks = [
        Attack({"name": "发呆", "damage": 0, "cost": [CardType.COLORLESS], "text": "抛掷1次硬币如果为正面，则回复这只宝可梦「10」点HP。"}),
        Attack({"name": "冲撞", "damage": 20, "cost": [CardType.WATER, CardType.COLORLESS], "text": ""})
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
            if action.attack == self.attacks[0]:
                if flip_coin(state) == Coin.HEAD:
                    yield from reduce_attack_action(action, state)
                    self.hp = min(self.hp + 10, 60)
            elif action.attack == self.attacks[1]:
                yield from reduce_attack_action(action, state)
        elif isinstance(action, RetreatAction):
            yield from reduce_retreat_action(action, state)

