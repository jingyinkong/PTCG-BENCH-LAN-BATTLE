"""博士的研究 - 支援者卡。将所有手牌丢弃，从牌库上方抽取7张。"""
from ptcg.core.action import UseSupporterAction
from ptcg.core.card import SupporterCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class SSH178ProfessorsResearch(SupporterCard):
    """博士的研究 - SSH 178"""
    def __init__(self):
        super().__init__()
        self.set_name = "SSH"
        self.number = "178"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "博士的研究"
        self.cardType = CardType.NONE
        self.text = "将自己的所有手牌丢弃，然后从牌库上方抽取7张。"

    def get_actions(self, state):
        player = current_player(state)
        actions = []
        if not player.supporterPlayedTurn:
            actions.append(UseSupporterAction(state.turn, self))
        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseSupporterAction):
            player = current_player(state)
            move_cards(self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state)
            hand_copy = list(player.hand)
            for card in hand_copy:
                move_cards(card, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state)
            draw_count = min(7, len(player.left))
            for _ in range(draw_count):
                move_cards(player.left[0], (player.id, CardPosition.LEFT), (player.id, CardPosition.HAND), state)
            player.supporterPlayedTurn = True
