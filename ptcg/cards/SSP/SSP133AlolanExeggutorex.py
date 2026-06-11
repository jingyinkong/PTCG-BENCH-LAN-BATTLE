"""阿罗拉 椰蛋树ex - SSP 133"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction, choose_card_actions
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import CardType, Coin, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_choose_card_actions, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.i18n import t as _t
from ptcg.utils.utils import check_energy, flip_coin, opponent_active, opponent_player


class SSP133AlolanExeggutorex(PokemonCard):
    """阿罗拉 椰蛋树ex - STAGE_1 宝可梦。HP: 300。"""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "SSP"
        self.number = "133"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "阿罗拉 椰蛋树ex"
        self.hp = 300
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.STAGE_1
        self.cardType = CardType.DRAGON
        self.retreat = [CardType.COLORLESS] * 3
        self.weakness = []
        self.resistance = []
        self.evolveFrom = ['蛋蛋']
        self.prize = 2
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.attacks = [
        Attack({"name": "热带狂热", "damage": 150, "cost": [CardType.GRASS, CardType.WATER], "text": "选择自己手牌中任意数量的基本能量，以任意方式附着于自己的宝可梦身上。"}),
        Attack({"name": "嗡嗡榍石", "damage": 0, "cost": [CardType.GRASS, CardType.WATER, CardType.FIGHTING], "text": "抛掷1次硬币如果为正面，则令对手战斗场上的【基础】宝可梦【昏厥】。如果为反面，则选择对手备战区中的1只【基础】宝可梦，令那只宝可梦【昏厥】。"})
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
                opponent = opponent_player(state)
                if flip_coin(state) == Coin.HEAD:
                    opponent.hasPokemonDead = True
                else:
                    basic_bench = [c for c in opponent.bench if c.stage == Stage.BASIC]
                    if basic_bench:
                        tips = _t("attack.alolan_exeggutor.benched_basic")
                        acts = choose_card_actions(opponent.id, opponent.id, 1, 1, basic_bench, tips=tips)
                        chosen = yield from reduce_choose_card_actions(acts, state)
                        if chosen:
                            chosen[0].hp = 0
                            opponent.hasPokemonDead = True
                yield from reduce_attack_action(action, state)
        elif isinstance(action, RetreatAction):
            yield from reduce_retreat_action(action, state)
