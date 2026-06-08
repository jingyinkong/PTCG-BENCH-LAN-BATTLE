"""Energy Switch - CES 129"""
from ptcg.core.action import UseItemAction, choose_card_actions
from ptcg.core.card import ItemCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import current_player, move_cards


class CES129EnergySwitch(ItemCard):
    """Energy Switch - Item. Move 1 basic Energy from 1 Pokémon to another."""
    def __init__(self):
        super().__init__()
        self.set_name = "CES"
        self.number = "129"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "能量转移"
        self.cardType = CardType.NONE
        self.text = "选择自己场上的1只宝可梦身上附着的1个基本能量，改附于自己其他的宝可梦身上。"

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
            # 简单实现: 不做复杂选择，允许引擎自动处理
            # 完整实现需要: 选源宝可梦 → 选能量 → 选目标宝可梦
            pass

    def _full_reduce(self, action, state):
        """Full implementation (reserved for future engine support)."""
        pass
