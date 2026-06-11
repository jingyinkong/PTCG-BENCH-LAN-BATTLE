"""古剑豹 - PAR 057"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, opponent_active


class PAR057ChienPao(PokemonCard):
    """古剑豹 - BASIC 宝可梦。HP: 120。"""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "PAR"
        self.number = "057"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "古剑豹"
        self.hp = 120
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.WATER
        self.retreat = [CardType.COLORLESS] * 1
        self.weakness = [CardType.METAL]
        self.resistance = []
        self.evolveFrom = []
        self.prize = 1
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.attacks = [
        Attack({"name": "冰雪生成", "damage": 0, "cost": [CardType.WATER], "text": "选择自己弃牌区中最多2张「基本【水】能量」，附着于自己的1只宝可梦身上。"}),
        Attack({"name": "愤怒利刃", "damage": 130, "cost": [CardType.WATER, CardType.WATER, CardType.COLORLESS], "text": "选择这只宝可梦身上附着的2个能量，放于弃牌区。"})
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
