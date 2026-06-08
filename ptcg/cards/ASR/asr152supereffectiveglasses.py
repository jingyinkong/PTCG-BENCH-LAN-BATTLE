"""Supereffective Glasses - ASR 152"""
from ptcg.core.action import UseItemAction
from ptcg.core.card import ToolCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class ASR152SupereffectiveGlasses(ToolCard):
    """Supereffective Glasses - Tool."""
    def __init__(self):
        super().__init__()
        self.set_name = "ASR"
        self.number = "152"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "超群眼镜"
        self.cardType = CardType.NONE
        self.text = "身上放有这张卡牌的宝可梦使用招式的伤害，在计算对手战斗宝可梦的弱点时，其弱点按照「x3」计算。"

    def get_actions(self, state):
        actions = []
        player = current_player(state)
        actions.append(UseItemAction(player.id, self))
        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseItemAction):
            player = current_player(state)
            move_cards(self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state)
