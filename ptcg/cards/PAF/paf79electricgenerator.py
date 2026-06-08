"""Electric Generator - PAF 079"""
from ptcg.core.action import UseItemAction, choose_card_actions
from ptcg.core.card import ItemCard
from ptcg.core.enums import CardPosition, CardType, EnergyType, SuperType
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import current_player, move_cards
from ptcg.i18n import t as _t


class PAF079ElectricGenerator(ItemCard):
    """Electric Generator - Item. Look at top 5 cards, attach any Lightning Energy found to Benched L Pokémon."""
    def __init__(self):
        super().__init__()
        self.set_name = "PAF"
        self.number = "079"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "电气发生器"
        self.cardType = CardType.NONE
        self.text = "查看自己牌库上方5张卡牌，选择其中任意数量的【雷】能量，以任意方式附着于备战区的【雷】宝可梦身上。将剩余卡牌放回牌库并重洗。"

    def get_actions(self, state):
        actions = []
        player = current_player(state)
        if self in player.hand and len(player.left) >= 1:
            actions.append(UseItemAction(player.id, self))
        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseItemAction):
            player = current_player(state)
            move_cards(self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state)
            look_count = min(5, len(player.left))
            looked = [player.left[i] for i in range(look_count)]
            lightning_energies = [c for c in looked if c.superType == SuperType.ENERGY and hasattr(c, "provides") and "LIGHTNING" in str(c.provides)]
            if lightning_energies and player.bench:
                tips = _t("item.electric_generator")
                actions = choose_card_actions(player.id, player.id, 0, len(lightning_energies), lightning_energies, tips=tips, source=self)
                chosen = yield from reduce_choose_card_actions(actions, state)
                if chosen:
                    for energy in chosen:
                        if energy in player.left:
                            move_cards(energy, (player.id, CardPosition.LEFT), (player.id, CardPosition.HAND), state)
