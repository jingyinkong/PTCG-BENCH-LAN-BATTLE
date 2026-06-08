"""Hisuian Electrode V - SP 294"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, opponent_active


class SP294HisuianElectrodeV(PokemonCard):
    """Hisuian Electrode V - BASIC Pokemon. HP: 210."""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "SP"
        self.number = "294"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "洗翠 顽皮雷弹V"
        self.hp = 210
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.GRASS
        self.retreat = [CardType.COLORLESS] * 1
        self.weakness = [CardType.FIRE]
        self.resistance = []
        self.evolveFrom = []
        self.prize = 2
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.attacks = [
        Attack({"name": "暴躁炸弹", "damage": 100, "cost": [CardType.COLORLESS], "text": "造成这只宝可梦所处于的特殊状态数量x100点伤害。"}),
        Attack({"name": "日光射击", "damage": 120, "cost": [CardType.GRASS, CardType.COLORLESS], "text": "将附着于这只宝可梦身上的能量，全部放于弃牌区。"})
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
