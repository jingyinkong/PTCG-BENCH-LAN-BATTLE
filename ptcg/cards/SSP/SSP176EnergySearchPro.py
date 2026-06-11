"""能量输送PRO - SSP 176"""
from ptcg.core.action import UseItemAction
from ptcg.core.card import ItemCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class SSP176EnergySearchPro(ItemCard):
    """能量输送PRO - 道具卡。"""
    def __init__(self):
        super().__init__()
        self.set_name = "SSP"
        self.number = "176"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "能量输送PRO"
        self.cardType = CardType.NONE
        self.text = "从自己牌库中，选择任意数量的属性各不相同的基本能量，在给对手看过之后，加入手牌，并重洗牌库。"

    def get_actions(self, state):
        actions = []
        player = current_player(state)
        actions.append(UseItemAction(player.id, self))
        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseItemAction):
            player = current_player(state)
            move_cards(self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state)
            yield None