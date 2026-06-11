"""梅洛可 - PAR 167"""
from ptcg.core.action import UseSupporterAction
from ptcg.core.card import SupporterCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class PAR167Mela(SupporterCard):
    """梅洛可 - 支援者卡。"""
    def __init__(self):
        super().__init__()
        self.set_name = "PAR"
        self.number = "167"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "梅洛可"
        self.cardType = CardType.NONE
        self.text = "这张卡牌，只有在上一个对手的回合，自己的宝可梦【昏厥】时才可使用。  选择自己弃牌区中的1张「基本【火】能量」，附着于自己的宝可梦身上。然后，从牌库上方抽取卡牌，直到自己的手牌变为6张为止。"

    def get_actions(self, state):
        actions = []
        player = current_player(state)
        if not player.supporterPlayedTurn:
            actions.append(UseSupporterAction(state.turn, self))
        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseSupporterAction):
            player = current_player(state)
            move_cards(self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state)
            player.supporterPlayedTurn = True
            yield None