"""Technical Machine: Devolution - PAR 177"""
from ptcg.core.action import UseItemAction
from ptcg.core.card import ToolCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class PAR177TechnicalMachineDevolution(ToolCard):
    """Technical Machine: Devolution - Tool."""
    def __init__(self):
        super().__init__()
        self.set_name = "PAR"
        self.number = "177"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "招式学习器 退化"
        self.cardType = CardType.NONE
        self.text = "身上放有这张卡牌的宝可梦，可以使用这张卡牌上的招式。[需要满足使用招式所需能量。] 放于宝可梦身上的这张卡牌，将在自己的回合结束时被放于弃牌区。  【无】 退化 从对手所有已经进化的宝可梦身上，各移除1张「进化卡」使其退化。将被移除的卡牌，放回对手的手牌。"

    def get_actions(self, state):
        actions = []
        player = current_player(state)
        actions.append(UseItemAction(player.id, self))
        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseItemAction):
            player = current_player(state)
            move_cards(self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state)
