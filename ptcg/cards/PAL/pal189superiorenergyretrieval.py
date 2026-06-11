"""超级能量回收 - PAL 189"""
from ptcg.core.action import UseItemAction
from ptcg.core.card import ItemCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class PAL189SuperiorEnergyRetrieval(ItemCard):
    """超级能量回收 - 道具卡。"""
    def __init__(self):
        super().__init__()
        self.set_name = "PAL"
        self.number = "189"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "超级能量回收"
        self.cardType = CardType.NONE
        self.text = "这张卡牌，只有将自己的2张手牌放于弃牌区后才可使用。  选择自己弃牌区中最多4张基本能量，在给对手看过之后，加入手牌。（无法选择因为这张卡牌的效果而被放于弃牌区的能量。）"

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
            yield None