"""菜种的活力 - ASR 143"""
from ptcg.core.action import UseSupporterAction
from ptcg.core.card import SupporterCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class ASR143GardeniasVigor(SupporterCard):
    """菜种的活力 - 支援者卡。"""
    def __init__(self):
        super().__init__()
        self.set_name = "ASR"
        self.number = "143"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "菜种的活力"
        self.cardType = CardType.NONE
        self.text = "从自己牌库上方抽取2张卡牌。然后，选择自己手牌中最多2张【草】能量，附着于1只备战宝可梦身上。"

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