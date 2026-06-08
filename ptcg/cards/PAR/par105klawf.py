"""Klawf - PAR 105"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, opponent_active


class PAR105Klawf(PokemonCard):
    """Klawf - BASIC Pokemon. HP: 120."""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "PAR"
        self.number = "105"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "毛崖蟹"
        self.hp = 120
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.FIGHTING
        self.retreat = [CardType.COLORLESS] * 3
        self.weakness = [CardType.GRASS]
        self.resistance = []
        self.evolveFrom = []
        self.prize = 1
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.attacks = [
        Attack({"name": "歇斯底里巨钳", "damage": 30, "cost": [CardType.COLORLESS, CardType.COLORLESS], "text": "如果这只宝可梦处于特殊状态的话，则追加造成160伤害。"}),
        Attack({"name": "沸腾压制", "damage": 80, "cost": [CardType.FIGHTING, CardType.FIGHTING], "text": "令这只宝可梦陷入【灼伤】状态。"})
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
