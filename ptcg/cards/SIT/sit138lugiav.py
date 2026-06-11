"""洛奇亚V - SIT 138"""
from ptcg.core.action import AttackAction, DiscardStadiumAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import AbilityType, CardPosition, CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import auto_end_turn, check_energy, current_player, move_cards, opponent_active


class SIT138LugiaV(PokemonCard):
    """洛奇亚V - BASIC 宝可梦。HP: 220。"""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "SIT"
        self.number = "138"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "洛奇亚V"
        self.hp = 220
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.COLORLESS
        self.retreat = [CardType.COLORLESS] * 2
        self.weakness = [CardType.LIGHTNING]
        self.resistance = [CardType.FIGHTING]
        self.evolveFrom = []
        self.prize = 2
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.attacks = [
        Attack({"name": "读风", "damage": 0, "cost": [CardType.COLORLESS], "text": "将自己的1张手牌放于弃牌区。然后，从自己牌库上方抽取3张卡牌。"}),
        Attack({"name": "气旋俯冲", "damage": 130, "cost": [CardType.COLORLESS, CardType.COLORLESS, CardType.COLORLESS, CardType.COLORLESS], "text": "若希望，可将场上的竞技场放于弃牌区。"})
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
            if action.attack == self.attacks[0]:
                player = current_player(state)
                move_cards(player.hand[0] if player.hand else [], (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state)
                yield from reduce_attack_action(action, state)
            elif action.attack == self.attacks[1]:
                yield from reduce_attack_action(action, state, auto_end_turn=False)
                player = current_player(state)
                if len(state.stadium) > 0:
                    old_stadium = state.stadium[0]
                    old_stadium.reduce_action(DiscardStadiumAction(player.id, old_stadium), state)
                auto_end_turn(state)
        elif isinstance(action, RetreatAction):
            yield from reduce_retreat_action(action, state)

