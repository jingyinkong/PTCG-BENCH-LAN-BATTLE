"""高级球 - 道具卡。弃2张手牌后，从牌库搜索一张宝可梦加入手牌。"""
from ptcg.core.action import UseItemAction, choose_card_actions
from ptcg.core.card import ItemCard
from ptcg.core.enums import CardPosition, CardType, SuperType
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import current_player, move_cards, shuffle_cards
from ptcg.i18n import t as _t


class SLG68UltraBall(ItemCard):
    """高级球 - SLG 068"""
    def __init__(self):
        super().__init__()
        self.set_name = "SLG"
        self.number = "068"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "高级球"
        self.cardType = CardType.NONE
        self.text = "只有在自己弃掉2张手牌后才可使用。从自己的牌库中选择一张宝可梦，在给对手看过后加入手牌。然后重洗牌库。"

    def get_actions(self, state):
        actions = []
        player = current_player(state)
        # 手中至少需要3张牌（含本牌+2张要弃的）
        if len(player.hand) >= 3:
            actions.append(UseItemAction(state.turn, self))
        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseItemAction):
            player = current_player(state)
            # 从牌库中筛选所有宝可梦
            getCards = [card for card in player.left if card.superType == SuperType.POKEMON]
            # 先将自身弃入弃牌堆
            move_cards(action.source, (player.id, CardPosition.HAND),
                       (player.id, CardPosition.DISCARD), state)
            # 选择2张手牌弃掉
            discardCards = player.hand
            tips = _t("item.ultra_ball.discard")
            actions = choose_card_actions(player.id, player.id, 2, 2, discardCards, tips=tips, source=self)
            chosen_card = yield from reduce_choose_card_actions(actions, state)
            if all(card in player.hand for card in chosen_card):
                move_cards(chosen_card, (player.id, CardPosition.HAND),
                           (player.id, CardPosition.DISCARD), state)
            else:
                raise ValueError(f"无效操作: {action}")
            # 从牌库中选择一张宝可梦加入手牌
            tips = _t("item.ultra_ball.search")
            actions = choose_card_actions(player.id, player.id, 0, 1, getCards, tips=tips, source=self)
            chosen_card = yield from reduce_choose_card_actions(actions, state)
            if all(card in player.left for card in chosen_card):
                move_cards(chosen_card, (player.id, CardPosition.LEFT),
                           (player.id, CardPosition.HAND), state)
            else:
                raise ValueError(f"无效操作: {action}")
            shuffle_cards(player.left)
