"""不服输头带 - SVI 169"""
from ptcg.core.action import UseItemAction
from ptcg.core.card import ToolCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class SVI169DefianceBand(ToolCard):
    """不服输头带 - 宝可梦道具卡。"""
    def __init__(self):
        super().__init__()
        self.set_name = "SVI"
        self.number = "169"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "不服输头带"
        self.cardType = CardType.NONE
        self.text = "如果自己的剩余奖赏卡张数，比对手的剩余奖赏卡张数多的话，则身上放有这张卡牌的宝可梦所使用的招式，给对手的战斗宝可梦造成的伤害「+30」。"

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
