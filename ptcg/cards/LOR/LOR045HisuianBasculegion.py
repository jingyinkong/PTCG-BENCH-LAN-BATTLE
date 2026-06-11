"""洗翠 幽尾玄鱼 - LOR 045"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, opponent_active


class LOR045HisuianBasculegion(PokemonCard):
    """洗翠 幽尾玄鱼 - STAGE_1 宝可梦。HP: 110。"""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "LOR"
        self.number = "045"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "洗翠 幽尾玄鱼"
        self.hp = 110
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.STAGE_1
        self.cardType = CardType.WATER
        self.retreat = [CardType.COLORLESS] * 1
        self.weakness = [CardType.LIGHTNING]
        self.resistance = []
        self.evolveFrom = ['洗翠 野蛮鲈鱼']
        self.prize = 1
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.attacks = [
        Attack({"name": "魂灵回游", "damage": 20, "cost": [CardType.COLORLESS], "text": "将自己弃牌区中的所有基本能量给对手查看，造成其张数x20点伤害。然后，将给对手查看过的能量放回牌库并重洗牌库。"}),
        Attack({"name": "水流射击", "damage": 70, "cost": [CardType.WATER], "text": "选择附着于这只宝可梦身上的1个能量，放于弃牌区。"})
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
