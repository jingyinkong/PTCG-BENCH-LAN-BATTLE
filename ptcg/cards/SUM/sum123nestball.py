"""巢穴球 - 道具卡。从牌库搜索一张基础宝可梦放到备战区，然后洗牌。"""
from ptcg.core.action import UseItemAction, choose_card_actions
from ptcg.core.card import ItemCard
from ptcg.core.enums import (
    CardPosition, CardType, PokemonPosition, Stage, SuperType
)
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import current_player, move_cards, shuffle_cards
from ptcg.i18n import t as _t


class SUM123NestBall(ItemCard):
    """巢穴球 - SUM 123"""
    def __init__(self):
        super().__init__()
        self.set_name = "SUM"
        self.number = "123"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "巢穴球"
        self.cardType = CardType.NONE
        self.text = "从自己的牌库中选择一张基础宝可梦，放置于备战区。然后重洗牌库。"

    def get_actions(self, state):
        player = current_player(state)
        actions = []
        # 备战区有空位时才可使用
        if player.benchSize - len(player.bench) >= 1:
            actions.extend([UseItemAction(state.turn, self)])
        return actions

    def reduce_action(self, action, state):
        player = current_player(state)
        # 从牌库中筛选基础宝可梦
        cards = [
            card for card in player.left
            if card.superType == SuperType.POKEMON and card.stage == Stage.BASIC
        ]
        if isinstance(action, UseItemAction):
            # 将自身弃入弃牌堆
            move_cards(
                self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state
            )
            # 让玩家选择一张基础宝可梦
            tips = _t("item.nest_ball")
            actions = choose_card_actions(player.id, player.id, 0, 1, cards, tips=tips, source=self)
            chosen_card = yield from reduce_choose_card_actions(actions, state)
            if len(chosen_card) == 0:
                pass
            elif len(chosen_card) == 1 and all(card in player.left for card in chosen_card):
                move_cards(chosen_card, (player.id, CardPosition.LEFT),
                           (player.id, CardPosition.BENCH), state)
                chosen_card[0].position = PokemonPosition.BENCH
            else:
                raise ValueError(f"无效操作: {action}")
            shuffle_cards(player.left)
