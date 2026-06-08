"""Energy Retrieval - SUM 116"""
from ptcg.core.action import UseItemAction, choose_card_actions
from ptcg.core.card import ItemCard
from ptcg.core.enums import CardPosition, CardType, EnergyType, SuperType
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import current_player, move_cards
from ptcg.i18n import t as _t


class SUM116EnergyRetrieval(ItemCard):
    """Energy Retrieval - Item. Get up to 2 basic Energy from discard to hand."""
    def __init__(self):
        super().__init__()
        self.set_name = "SUM"
        self.number = "116"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "能量回收"
        self.cardType = CardType.NONE
        self.text = "选择自己弃牌区中最多2张基本能量，在给对手看过之后，加入手牌。"

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
            # 从弃牌区选最多2张基本能量加入手牌
            basic_energies = [
                c for c in player.discard
                if c.superType == SuperType.ENERGY and c.energyType == EnergyType.BASIC
            ]
            if basic_energies:
                tips = _t("item.energy_retrieval")
                actions = choose_card_actions(
                    player.id, player.id, 0, min(2, len(basic_energies)),
                    basic_energies, tips=tips, source=self
                )
                chosen = yield from reduce_choose_card_actions(actions, state)
                if chosen:
                    for card in chosen:
                        if card in player.discard:
                            move_cards(card, (player.id, CardPosition.DISCARD), (player.id, CardPosition.HAND), state)
