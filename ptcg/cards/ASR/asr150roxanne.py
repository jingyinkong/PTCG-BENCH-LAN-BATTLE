"""Roxanne - ASR 150"""
from ptcg.core.action import UseSupporterAction
from ptcg.core.card import SupporterCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards, opponent_player, shuffle_cards


class ASR150Roxanne(SupporterCard):
    """Roxanne - Supporter. Usable when opponent has ≤3 prizes.
    Shuffle hand into deck, draw 6. Opponent draws 2."""
    def __init__(self):
        super().__init__()
        self.set_name = "ASR"
        self.number = "150"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "罗莎"
        self.cardType = CardType.NONE
        self.text = "只有对手剩余奖赏卡为3张以下时才可使用。将所有手牌放回牌库并重洗。然后，从牌库上方抽取6张。对手从牌库上方抽取2张。"

    def get_actions(self, state):
        actions = []
        player = current_player(state)
        opponent = opponent_player(state)
        if not player.supporterPlayedTurn and len(opponent.prize) <= 3:
            actions.append(UseSupporterAction(state.turn, self))
        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseSupporterAction):
            player = current_player(state)
            opponent = opponent_player(state)
            move_cards(self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state)
            # 手牌放回牌库并重洗
            for card in list(player.hand):
                move_cards(card, (player.id, CardPosition.HAND), (player.id, CardPosition.LEFT), state)
            shuffle_cards(player.left)
            # 抽6张
            for _ in range(min(6, len(player.left))):
                move_cards(player.left[0], (player.id, CardPosition.LEFT), (player.id, CardPosition.HAND), state)
            # 对手抽2张
            for _ in range(min(2, len(opponent.left))):
                move_cards(opponent.left[0], (opponent.id, CardPosition.LEFT), (opponent.id, CardPosition.HAND), state)
            player.supporterPlayedTurn = True
