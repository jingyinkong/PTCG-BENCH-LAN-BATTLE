"""Earthen Vessel - PRE 106"""
from ptcg.core.action import UseItemAction, choose_card_actions
from ptcg.core.card import ItemCard
from ptcg.core.enums import CardPosition, CardType, EnergyType, SuperType
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import current_player, move_cards, shuffle_cards
from ptcg.i18n import t as _t


class PRE106EarthenVessel(ItemCard):
    """Earthen Vessel - Item. Discard 1 card, search deck for up to 2 basic Energy, reveal and add to hand."""
    def __init__(self):
        super().__init__()
        self.set_name = "PRE"
        self.number = "106"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "大地之器"
        self.cardType = CardType.NONE
        self.text = "将自己的1张手牌丢于弃牌区。（若无法丢弃则无法使用。）选择自己牌库中最多2张基本能量，在给对手看过之后，加入手牌。并重洗牌库。"

    def get_actions(self, state):
        actions = []
        player = current_player(state)
        if self in player.hand and len(player.hand) >= 2:  # need 1 extra to discard
            actions.append(UseItemAction(player.id, self))
        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseItemAction):
            player = current_player(state)
            move_cards(self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state)
            # 弃1张手牌
            if player.hand:
                move_cards(player.hand[0], (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state)
            # 从牌库选最多2张基本能量
            basic_energies = [c for c in player.left if c.superType == SuperType.ENERGY and c.energyType == EnergyType.BASIC]
            if basic_energies:
                tips = _t("item.earthen_vessel.search")
                actions = choose_card_actions(player.id, player.id, 0, min(2, len(basic_energies)), basic_energies, tips=tips, source=self)
                chosen = yield from reduce_choose_card_actions(actions, state)
                if chosen:
                    for c in chosen:
                        if c in player.left:
                            move_cards(c, (player.id, CardPosition.LEFT), (player.id, CardPosition.HAND), state)
            shuffle_cards(player.left)
