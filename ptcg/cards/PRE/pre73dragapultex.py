"""Dragapult ex - PRE 073"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, opponent_active


class PRE073Dragapultex(PokemonCard):
    """Dragapult ex - STAGE_2 Pokemon. HP: 320."""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "PRE"
        self.number = "073"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "多龙巴鲁托ex"
        self.hp = 320
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.STAGE_2
        self.cardType = CardType.DRAGON
        self.retreat = [CardType.COLORLESS] * 1
        self.weakness = []
        self.resistance = []
        self.evolveFrom = ['多龙奇']
        self.prize = 2
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.attacks = [
        Attack({"name": "喷射头击", "damage": 70, "cost": [CardType.COLORLESS], "text": ""}),
        Attack({"name": "幻影潜袭", "damage": 200, "cost": [CardType.FIRE, CardType.PSYCHIC], "text": "将6个伤害指示物，以任意方式放置于对手的备战宝可梦身上。"})
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
