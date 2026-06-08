"""奇树 - 支援者卡。双方将手牌放回牌库底部，然后抽取与奖赏卡张数相同的牌。"""
from ptcg.core.action import UseSupporterAction
from ptcg.core.card import SupporterCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards, opponent_player, shuffle_cards


class PAL185Iono(SupporterCard):
    """奇树 - PAL 185"""
    def __init__(self):
        super().__init__()
        self.set_name = "PAL"
        self.number = "185"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "奇树"
        self.cardType = CardType.NONE
        self.text = "双方玩家将手牌全部放回牌库并重洗。然后，各自从牌库抽取与自己的剩余奖赏卡张数相同的牌。"

    def get_actions(self, state):
        player = current_player(state)
        actions = []
        if not player.supporterPlayedTurn:
            actions.append(UseSupporterAction(state.turn, self))
        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseSupporterAction):
            player = current_player(state)
            opponent = opponent_player(state)
            move_cards(self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state)
            if player.hand:
                shuffle_cards(player.hand)
                move_cards(player.hand[:], (player.id, CardPosition.HAND), (player.id, CardPosition.LEFT), state)
            cards_to_draw = len(player.prize)
            if cards_to_draw > 0:
                draw_cards = player.left[:cards_to_draw]
                move_cards(draw_cards, (player.id, CardPosition.LEFT), (player.id, CardPosition.HAND), state)
            if opponent.hand:
                shuffle_cards(opponent.hand)
                move_cards(opponent.hand[:], (opponent.id, CardPosition.HAND), (opponent.id, CardPosition.LEFT), state)
            opponent_cards_to_draw = len(opponent.prize)
            if opponent_cards_to_draw > 0:
                draw_cards = opponent.left[:opponent_cards_to_draw]
                move_cards(draw_cards, (opponent.id, CardPosition.LEFT), (opponent.id, CardPosition.HAND), state)
            shuffle_cards(player.left)
            shuffle_cards(opponent.left)
        player.supporterPlayedTurn = True
