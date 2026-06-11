"""坚硬束带 - MEW 165"""
from ptcg.core.action import UseItemAction
from ptcg.core.card import ToolCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class MEW165RigidBand(ToolCard):
    """坚硬束带 - 宝可梦道具卡。"""
    def __init__(self):
        super().__init__()
        self.set_name = "MEW"
        self.number = "165"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "坚硬束带"
        self.cardType = CardType.NONE
        self.text = "身上放有这张卡牌的【1阶进化】宝可梦，受到对手宝可梦的招式的伤害「-30」。"

    def get_actions(self, state):
        actions = []
        player = current_player(state)
        actions.append(UseItemAction(player.id, self))
        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseItemAction):
            player = current_player(state)
            move_cards(self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state)
