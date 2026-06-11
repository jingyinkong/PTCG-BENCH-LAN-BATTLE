"""放逐吸尘器 - CRZ 135"""
from ptcg.core.action import UseItemAction
from ptcg.core.card import ItemCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class CRZ135LostVacuum(ItemCard):
    """放逐吸尘器 - 道具卡。"""
    def __init__(self):
        super().__init__()
        self.set_name = "CRZ"
        self.number = "135"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "放逐吸尘器"
        self.cardType = CardType.NONE
        self.text = "这张卡牌，只有将自己的1张手牌，放于放逐区后才可使用。  选择放于双方场上宝可梦身上的「宝可梦道具」以及场上的「竞技场」中的1张，放于放逐区。"

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