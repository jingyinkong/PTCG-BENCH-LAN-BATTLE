"""Arven - SVI 166"""
from ptcg.core.action import UseSupporterAction, choose_card_actions
from ptcg.core.card import SupporterCard
from ptcg.core.enums import CardPosition, CardType, SuperType
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import current_player, move_cards, shuffle_cards
from ptcg.i18n import t as _t


class SVI166Arven(SupporterCard):
    """Arven - Supporter. Search deck for 1 Item and 1 Tool, reveal and add to hand."""
    def __init__(self):
        super().__init__()
        self.set_name = "SVI"
        self.number = "166"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "阿克罗玛"
        self.cardType = CardType.NONE
        self.text = "选择自己牌库中的1张物品卡与1张宝可梦道具，在给对手看过之后，加入手牌。并重洗牌库。"

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
            # 选1张物品卡
            items = [c for c in player.left if c.superType == SuperType.TRAINER and ("ItemCard" in str(type(c).__mro__) or "item" in str(type(c)).lower())]
            if items:
                tips = _t("supporter.arven.item")
                actions = choose_card_actions(player.id, player.id, 0, 1, items, tips=tips, source=self)
                chosen = yield from reduce_choose_card_actions(actions, state)
                if chosen and chosen[0] in player.left:
                    move_cards(chosen[0], (player.id, CardPosition.LEFT), (player.id, CardPosition.HAND), state)
            # 选1张道具
            tools = [c for c in player.left if c.superType == SuperType.TRAINER and "ToolCard" in str(type(c).__mro__)]
            if tools:
                tips = _t("supporter.arven.tool")
                actions = choose_card_actions(player.id, player.id, 0, 1, tools, tips=tips, source=self)
                chosen = yield from reduce_choose_card_actions(actions, state)
                if chosen and chosen[0] in player.left:
                    move_cards(chosen[0], (player.id, CardPosition.LEFT), (player.id, CardPosition.HAND), state)
            shuffle_cards(player.left)
            player.supporterPlayedTurn = True
