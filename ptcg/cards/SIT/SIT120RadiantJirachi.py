"""光辉基拉祈 - SIT 120"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import CardType, Coin, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, flip_coin, opponent_player, opponent_active


class SIT120RadiantJirachi(PokemonCard):
    """光辉基拉祈 - BASIC 宝可梦。HP: 90。"""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "SIT"
        self.number = "120"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "光辉基拉祈"
        self.hp = 90
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.RADIANT
        self.stage = Stage.BASIC
        self.cardType = CardType.METAL
        self.retreat = [CardType.COLORLESS] * 1
        self.weakness = [CardType.FIRE]
        self.resistance = [CardType.GRASS]
        self.evolveFrom = []
        self.prize = 1
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.attacks = [
        Attack({"name": "星之灾厄", "damage": 0, "cost": [CardType.COLORLESS, CardType.COLORLESS], "text": "抛掷2次硬币，如果全部都是正面的话，则使对手的战斗宝可梦【昏厥】。"})
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
            coin1 = flip_coin(state)
            coin2 = flip_coin(state)
            if coin1 == Coin.HEAD and coin2 == Coin.HEAD:
                opponent = opponent_player(state)
                opponent.hasPokemonDead = True
            yield from reduce_attack_action(action, state)
        elif isinstance(action, RetreatAction):
            yield from reduce_retreat_action(action, state)
