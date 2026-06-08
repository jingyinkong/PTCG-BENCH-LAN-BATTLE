"""Vitality Band - SSH 185"""
from ptcg.core.action import UseItemAction
from ptcg.core.card import ToolCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class SSH185VitalityBand(ToolCard):
    """Vitality Band - Tool."""
    def __init__(self):
        super().__init__()
        self.set_name = "SSH"
        self.number = "185"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "活力头带"
        self.cardType = CardType.NONE
        self.text = "身上放有这张卡牌的宝可梦所使用的招式，给对手的战斗宝可梦造成的伤害「+10」。"

    def get_actions(self, state):
        actions = []
        player = current_player(state)
        actions.append(UseItemAction(player.id, self))
        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseItemAction):
            player = current_player(state)
            move_cards(self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state)
