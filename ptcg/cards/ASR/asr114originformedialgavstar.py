"""Origin Forme Dialga VSTAR - ASR 114"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, opponent_active


class ASR114OriginFormeDialgaVSTAR(PokemonCard):
    """Origin Forme Dialga VSTAR - BASIC Pokemon. HP: 280."""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "ASR"
        self.number = "114"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "起源帝牙卢卡VSTAR"
        self.hp = 280
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.METAL
        self.retreat = [CardType.COLORLESS] * 3
        self.weakness = [CardType.FIRE]
        self.resistance = [CardType.GRASS]
        self.evolveFrom = ['起源帝牙卢卡V']
        self.prize = 2
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.attacks = [
        Attack({"name": "金属爆破", "damage": 40, "cost": [CardType.COLORLESS], "text": "追加造成这只宝可梦身上附有的【钢】能量数量x40点伤害。"}),
        Attack({"name": "星耀时刻", "damage": 220, "cost": [CardType.METAL, CardType.METAL, CardType.METAL, CardType.METAL, CardType.COLORLESS], "text": "当这个回合结束时，自己的回合会再开始1次。[对战中，己方的VSTAR力量只能使用1次。]"})
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
