"""闪电鸟 - SVP 157"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import AbilityType, CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, opponent_active


class SVP157Zapdos(PokemonCard):
    """闪电鸟 - BASIC 宝可梦。HP: 110。"""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "SVP"
        self.number = "157"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "闪电鸟"
        self.hp = 110
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.LIGHTNING
        self.retreat = [CardType.COLORLESS] * 1
        self.weakness = [CardType.LIGHTNING]
        self.resistance = [CardType.FIGHTING]
        self.evolveFrom = []
        self.prize = 1
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.attacks = [
        Attack({"name": "追击伏特", "damage": 20, "cost": [CardType.LIGHTNING, CardType.COLORLESS], "text": "追加造成对手战斗宝可梦身上放置的伤害指示物数量x10伤害。"}),
        Attack({"name": "啄钻", "damage": 80, "cost": [CardType.LIGHTNING, CardType.COLORLESS, CardType.COLORLESS], "text": ""})
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

