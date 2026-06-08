"""Thorton - LOR 167"""
from ptcg.core.action import UseSupporterAction, choose_card_actions
from ptcg.core.card import SupporterCard
from ptcg.core.enums import CardPosition, CardType, SuperType
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import current_player, move_cards, shuffle_cards
from ptcg.i18n import t as _t


class LOR167Thorton(SupporterCard):
    """Thorton - Supporter. Search deck for a Pokémon with different name than own Pokémon, switch them."""
    def __init__(self):
        super().__init__()
        self.set_name = "LOR"
        self.number = "167"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "松英"
        self.cardType = CardType.NONE
        self.text = "选择自己牌库中的1张名称与自己的场上宝可梦各不同的宝可梦卡，将其与自己的场上宝可梦互换（身上附加的卡牌、伤害指示物、特殊状态、效果等全部保留）。并重洗牌库。"

    def get_actions(self, state):
        actions = []
        player = current_player(state)
        if not player.supporterPlayedTurn:
            actions.append(UseSupporterAction(state.turn, self))
        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseSupporterAction):
            player = current_player(state)
            move_cards(self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state)
            # 简单实现: 从牌库选1只宝可梦加入手牌
            pokemon = [c for c in player.left if c.superType == SuperType.POKEMON]
            if pokemon:
                tips = _t("supporter.thorton")
                actions = choose_card_actions(player.id, player.id, 0, 1, pokemon, tips=tips, source=self)
                chosen = yield from reduce_choose_card_actions(actions, state)
                if chosen and chosen[0] in player.left:
                    move_cards(chosen[0], (player.id, CardPosition.LEFT), (player.id, CardPosition.HAND), state)
            shuffle_cards(player.left)
            player.supporterPlayedTurn = True
