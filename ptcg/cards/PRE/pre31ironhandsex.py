"""Iron Hands ex - PRE 031"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, opponent_active


class PRE031IronHandsex(PokemonCard):
    """Iron Hands ex - BASIC Pokemon. HP: 230."""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "PRE"
        self.number = "031"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "铁臂膀ex"
        self.hp = 230
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.LIGHTNING
        self.retreat = [CardType.COLORLESS] * 4
        self.weakness = [CardType.FIGHTING]
        self.resistance = []
        self.evolveFrom = []
        self.prize = 2
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.attacks = [
        Attack({"name": "臂膀压制", "damage": 160, "cost": [CardType.LIGHTNING, CardType.LIGHTNING, CardType.COLORLESS], "text": ""}),
        Attack({"name": "多谢款待", "damage": 120, "cost": [CardType.LIGHTNING, CardType.COLORLESS, CardType.COLORLESS, CardType.COLORLESS], "text": "如果因为这个招式的伤害，对手的宝可梦【昏厥】的话，则多拿取1张奖赏卡。"})
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
