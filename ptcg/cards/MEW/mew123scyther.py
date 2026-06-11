"""飞天螳螂 - MEW 123"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import AbilityType, CardPosition, CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, opponent_active


class MEW123Scyther(PokemonCard):
    """飞天螳螂 - BASIC 宝可梦。HP: 70。"""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "MEW"
        self.number = "123"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "飞天螳螂"
        self.hp = 70
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.GRASS
        self.retreat = [CardType.COLORLESS] * 0
        self.weakness = [CardType.FIRE]
        self.resistance = []
        self.evolveFrom = []
        self.prize = 1
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.attacks = [
        Attack({"name": "辅助斩", "damage": 20, "cost": [CardType.GRASS], "text": "选择自己弃牌区中的1张「基本【草】能量」，附着于备战宝可梦身上。"}),
        Attack({"name": "薄片利刃", "damage": 70, "cost": [CardType.GRASS, CardType.COLORLESS, CardType.COLORLESS], "text": ""})
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

