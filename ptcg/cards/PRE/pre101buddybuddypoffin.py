"""友好宝芬 - 道具卡。从牌库搜索最多2张HP 70以下的基础宝可梦放置到备战区。"""
from ptcg.core.action import UseItemAction, choose_card_actions
from ptcg.core.card import ItemCard
from ptcg.core.enums import (
    CardPosition, CardType, PokemonPosition, Stage, SuperType
)
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import current_player, move_cards, shuffle_cards
from ptcg.i18n import t as _t


class PRE101BuddyBuddyPoffin(ItemCard):
    """友好宝芬 - PRE 101"""
    def __init__(self):
        super().__init__()
        self.set_name = "PRE"
        self.number = "101"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "友好宝芬"
        self.cardType = CardType.NONE
        self.text = "从自己的牌库中选择最多2张HP为70以下的基础宝可梦，放置于备战区。然后重洗牌库。"

    def get_actions(self, state):
        player = current_player(state)
        actions = []
        # 备战区有空位时才可使用
        if player.benchSize - len(player.bench) >= 1:
            actions.extend([UseItemAction(state.turn, self)])
        return actions

    def reduce_action(self, action, state):
        player = current_player(state)
        # 从牌库中筛选HP为70以下的基础宝可梦
        cards = [
            card for card in player.left
            if card.superType == SuperType.POKEMON and card.stage == Stage.BASIC and card.hp <= 70
        ]
        bench_left = player.benchSize - len(player.bench)
        if isinstance(action, UseItemAction):
            tips = _t("item.buddy_buddy_poffin").format(count=min(len(cards), bench_left, 2))
            actions = choose_card_actions(
                player.id, player.id, 0, min(len(cards), bench_left, 2),
                cards, tips=tips, source=self,
            )
            chosen_card = yield from reduce_choose_card_actions(actions, state)
            if all(card in player.left for card in chosen_card):
                # 将选中的宝可梦移动到备战区
                for card in chosen_card:
                    player.left.remove(card)
                    player.bench.append(card)
                    card.position = PokemonPosition.BENCH
                    card.cardPosition = CardPosition.BENCH
                for idx, card in enumerate(player.left):
                    card.index = idx + 1
                for idx, card in enumerate(player.bench):
                    card.index = idx + 1
            else:
                raise ValueError(f"无效操作: {action}")
            shuffle_cards(player.left)
            # 将自身弃入弃牌堆
            move_cards(self, (player.id, CardPosition.HAND),
                       (player.id, CardPosition.DISCARD), state)
