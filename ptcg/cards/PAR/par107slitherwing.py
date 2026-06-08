"""Slither Wing - PAR 107"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import CardPosition, CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import auto_end_turn, check_energy, current_player, move_cards, opponent_active, opponent_player


class PAR107SlitherWing(PokemonCard):
    """Slither Wing - BASIC Pokemon. HP: 140."""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "PAR"; self.number = "107"; self.id = f"{self.set_name}-{self.number}"
        self.name = "爬地翅"; self.hp = 140
        self.pokemonType = PokemonType.NORMAL; self.pokemonRule = PokemonRule.ANCIENT; self.stage = Stage.BASIC
        self.cardType = CardType.FIGHTING
        self.retreat = [CardType.COLORLESS]*2; self.weakness = [CardType.PSYCHIC]; self.resistance = []
        self.evolveFrom = []; self.prize = 1
        self.energy = []; self.attachment = []; self.evolved = []
        self.attacks = [
            Attack({"name": "踏平","damage": 0,"cost": [CardType.FIGHTING],"text": "将对手牌库上方1张卡牌放于弃牌区。"}),
            Attack({"name": "烫伤怒涛","damage": 120,"cost": [CardType.FIGHTING,CardType.FIGHTING,CardType.COLORLESS],"text": "给这只宝可梦也造成90伤害。令对手战斗宝可梦陷入灼伤状态。"})
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
        if isinstance(action, PlayPokemonAction): reduce_play_pokemon_action(action, state)
        elif isinstance(action, EvolvePokemonAction): reduce_evolve_pokemon_action(action, state)
        elif isinstance(action, RetreatAction): yield from reduce_retreat_action(action, state)
        elif isinstance(action, AttackAction):
            player = current_player(state)
            opponent = opponent_player(state)
            if action.attack.name == "踏平":
                # 弃对手牌库顶1张
                if opponent.left:
                    move_cards(opponent.left[0], (opponent.id, CardPosition.LEFT), (opponent.id, CardPosition.DISCARD), state)
                auto_end_turn(state)
            elif action.attack.name == "烫伤怒涛":
                # 自伤90
                self.hp -= 90
                yield from reduce_attack_action(action, state)
                auto_end_turn(state)
            else:
                yield from reduce_attack_action(action, state)
