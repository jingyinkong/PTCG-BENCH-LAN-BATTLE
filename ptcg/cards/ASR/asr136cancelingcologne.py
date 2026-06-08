"""Canceling Cologne - ASR 136"""
from ptcg.core.action import UseItemAction
from ptcg.core.card import ItemCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class ASR136CancelingCologne(ItemCard):
    """Canceling Cologne - Item. Until end of turn, opponent's Active has no Abilities."""
    def __init__(self):
        super().__init__()
        self.set_name = "ASR"
        self.number = "136"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "消除香水"
        self.cardType = CardType.NONE
        self.text = "在这个回合结束前，对手的战斗宝可梦的特性全部无效。"

    def get_actions(self, state):
        actions = []
        player = current_player(state)
        if self in player.hand:
            actions.append(UseItemAction(player.id, self))
        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseItemAction):
            player = current_player(state)
            move_cards(self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state)
            # 设置对手战斗宝可梦特性无效标记(引擎层面检查)
            player.opponentAbilityBlocked = True
