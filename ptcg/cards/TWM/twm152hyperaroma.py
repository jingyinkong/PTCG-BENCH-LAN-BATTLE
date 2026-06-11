"""高级香氛 - TWM 152"""
from ptcg.core.action import UseItemAction
from ptcg.core.card import ItemCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class TWM152HyperAroma(ItemCard):
    """高级香氛 - 道具卡。"""
    def __init__(self):
        super().__init__()
        self.set_name = "TWM"
        self.number = "152"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "高级香氛"
        self.cardType = CardType.NONE
        self.cardPosition = CardPosition.DECK
        self.text = "选择自己牌库中最多3张【1阶进化】宝可梦，在给对手看过之后，加入手牌。并重洗牌库。"

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