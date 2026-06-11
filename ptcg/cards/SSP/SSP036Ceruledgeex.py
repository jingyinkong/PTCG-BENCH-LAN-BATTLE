"""苍炎刃鬼ex - SSP 036"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, opponent_active


class SSP036Ceruledgeex(PokemonCard):
    """苍炎刃鬼ex - STAGE_1 宝可梦。HP: 270。"""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "SSP"
        self.number = "036"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "苍炎刃鬼ex"
        self.hp = 270
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.STAGE_1
        self.cardType = CardType.FIRE
        self.retreat = [CardType.COLORLESS] * 2
        self.weakness = [CardType.WATER]
        self.resistance = []
        self.evolveFrom = ['炭小侍']
        self.prize = 2
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.attacks = [
        Attack({"name": "深渊炽火", "damage": 30, "cost": [CardType.FIRE], "text": "追加造成自己弃牌区中能量张数x20伤害。"}),
        Attack({"name": "紫水晶之怒", "damage": 280, "cost": [CardType.FIRE, CardType.PSYCHIC, CardType.METAL], "text": "将这只宝可梦身上附着的能量，全部放于弃牌区。"})
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
