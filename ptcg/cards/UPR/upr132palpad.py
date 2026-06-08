"""Pal Pad - UPR 132"""
from ptcg.core.action import UseItemAction, choose_card_actions
from ptcg.core.card import ItemCard
from ptcg.core.enums import CardPosition, CardType, SuperType
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import current_player, move_cards, shuffle_cards
from ptcg.i18n import t as _t


class UPR132PalPad(ItemCard):
    """Pal Pad - Item. Shuffle up to 2 Supporter cards from discard into deck."""
    def __init__(self):
        super().__init__()
        self.set_name = "UPR"
        self.number = "132"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "朋友手册"
        self.cardType = CardType.NONE
        self.text = "选择自己弃牌区中最多2张支援者，在给对手看过之后，放回牌库并重洗。"

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
            supporters = [c for c in player.discard if c.superType == SuperType.TRAINER and "SupporterCard" in str(type(c).__mro__)]
            if supporters:
                tips = _t("item.pal_pad")
                actions = choose_card_actions(player.id, player.id, 0, min(2, len(supporters)), supporters, tips=tips, source=self)
                chosen = yield from reduce_choose_card_actions(actions, state)
                if chosen:
                    for c in chosen:
                        if c in player.discard:
                            move_cards(c, (player.id, CardPosition.DISCARD), (player.id, CardPosition.LEFT), state)
                    shuffle_cards(player.left)
