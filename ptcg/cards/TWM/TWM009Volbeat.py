"""电萤虫 - TWM 009"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, current_player, opponent_active


class TWM009Volbeat(PokemonCard):
    """电萤虫 - BASIC 宝可梦。HP: 70。"""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "TWM"
        self.number = "009"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "电萤虫"
        self.hp = 70
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.GRASS
        self.retreat = [CardType.COLORLESS] * 1
        self.weakness = [CardType.FIRE]
        self.resistance = []
        self.evolveFrom = []
        self.prize = 1
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.attacks = [
        Attack({"name": "快速信号", "damage": 0, "cost": [CardType.COLORLESS], "text": "这个招式，即使是先攻玩家的最初回合也可以使用。选择自己牌库中最多2张【基础】宝可梦，放于备战区。并重洗牌库。"}),
        Attack({"name": "合作攻击", "damage": 20, "cost": [CardType.COLORLESS, CardType.COLORLESS], "text": "如果自己的备战区中有「甜甜萤」的话，则追加造成60伤害。"})
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
            if action.attack == self.attacks[0]:
                yield from reduce_attack_action(action, state)
            elif action.attack == self.attacks[1]:
                player = current_player(state)
                has_illumise = any(
                    c for c in player.bench
                    if hasattr(c, 'name') and '甜甜萤' in c.name
                )
                if has_illumise:
                    action.attack.damage = 20 + 60
                yield from reduce_attack_action(action, state)
        elif isinstance(action, RetreatAction):
            yield from reduce_retreat_action(action, state)
