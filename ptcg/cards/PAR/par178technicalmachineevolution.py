"""招式学习器 进化 - PAR 178"""
from ptcg.core.action import UseItemAction
from ptcg.core.card import ToolCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class PAR178TechnicalMachineEvolution(ToolCard):
    """招式学习器 进化 - 宝可梦道具卡。"""
    def __init__(self):
        super().__init__()
        self.set_name = "PAR"
        self.number = "178"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "招式学习器 进化"
        self.cardType = CardType.NONE
        self.text = "身上放有这张卡牌的宝可梦，可以使用这张卡牌上的招式。[需要满足使用招式所需能量。] 放于宝可梦身上的这张卡牌，将在自己的回合结束时被放于弃牌区。  【无】 进化 选择自己最多2只备战宝可梦，从自己牌库中选择从该宝可梦进化而来的卡牌各1张，各放于其身上进行进化。并重洗牌库。"

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
