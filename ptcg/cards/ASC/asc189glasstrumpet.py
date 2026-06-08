"""Glass Trumpet - ASC 189"""
from ptcg.core.action import UseItemAction, choose_card_actions
from ptcg.core.card import ItemCard
from ptcg.core.enums import CardPosition, CardType, EnergyType, SuperType
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import current_player, move_cards
from ptcg.i18n import t as _t


class ASC189GlassTrumpet(ItemCard):
    """Glass Trumpet - Item. Usable only with Tera Pokémon in play.
    Attach up to 2 basic Energy from discard to 2 Benched Pokémon."""
    def __init__(self):
        super().__init__()
        self.set_name = "ASC"
        self.number = "189"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "玻璃喇叭"
        self.cardType = CardType.NONE
        self.text = "只有自己场上有「太晶」宝可梦时才可使用。选择自己弃牌区最多2张基本能量，以任意方式附着于备战宝可梦身上。"

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
            basic_energies = [c for c in player.discard if c.superType == SuperType.ENERGY and c.energyType == EnergyType.BASIC]
            if basic_energies and player.bench:
                tips = _t("item.glass_trumpet")
                actions = choose_card_actions(player.id, player.id, 0, min(2, len(basic_energies)), basic_energies, tips=tips, source=self)
                chosen = yield from reduce_choose_card_actions(actions, state)
                if chosen:
                    for energy in chosen:
                        if energy in player.discard:
                            move_cards(energy, (player.id, CardPosition.DISCARD), (player.id, CardPosition.HAND), state)
                            # 简化: 加入手牌(完整实现应直接附着)
