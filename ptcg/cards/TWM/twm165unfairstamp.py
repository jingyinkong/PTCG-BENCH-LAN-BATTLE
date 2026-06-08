"""Unfair Stamp - TWM 165"""
from ptcg.core.action import UseItemAction
from ptcg.core.card import ItemCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards, opponent_player, shuffle_cards


class TWM165UnfairStamp(ItemCard):
    """Unfair Stamp - Item. Usable when own Pokémon was Knocked Out last turn.
    Shuffle opponent's hand into deck, opponent draws based on own prizes."""
    def __init__(self):
        super().__init__()
        self.set_name = "TWM"
        self.number = "165"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "不公印章"
        self.cardType = CardType.NONE
        self.text = "这张卡牌，只有自己的宝可梦在对手的上个回合【昏厥】时才可使用。将对手的所有手牌放回牌库并重洗。然后，对手从牌库上方抽取与自己剩余奖赏卡相同张数的卡牌。"

    def get_actions(self, state):
        actions = []
        player = current_player(state)
        if self in player.hand:
            actions.append(UseItemAction(player.id, self))
        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseItemAction):
            player = current_player(state)
            opponent = opponent_player(state)
            move_cards(self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state)
            # 对手手牌放回牌库并重洗
            for card in list(opponent.hand):
                move_cards(card, (opponent.id, CardPosition.HAND), (opponent.id, CardPosition.LEFT), state)
            shuffle_cards(opponent.left)
            # 对手抽取与自己剩余奖赏卡相同张数
            draw_count = min(len(player.prize), len(opponent.left))
            for _ in range(draw_count):
                move_cards(opponent.left[0], (opponent.id, CardPosition.LEFT), (opponent.id, CardPosition.HAND), state)
