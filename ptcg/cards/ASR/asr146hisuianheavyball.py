"""Hisuian Heavy Ball - ASR 146"""
from ptcg.core.action import UseItemAction, choose_card_actions
from ptcg.core.card import ItemCard
from ptcg.core.enums import CardPosition, CardType, SuperType
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import current_player, move_cards, shuffle_cards
from ptcg.i18n import t as _t


class ASR146HisuianHeavyBall(ItemCard):
    """Hisuian Heavy Ball - Item. Look at prize cards face-down, take 1 Basic Pokémon from them, replace with this card."""
    def __init__(self):
        super().__init__()
        self.set_name = "ASR"
        self.number = "146"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "洗翠的沉重球"
        self.cardType = CardType.NONE
        self.text = "查看自己所有反面朝上的奖赏卡，选择其中1张基础宝可梦，给对手看过之后，与这张「洗翠的沉重球」卡牌互换，加入手牌。（将看过的奖赏卡恢复反面朝上。）"

    def get_actions(self, state):
        actions = []
        player = current_player(state)
        if self in player.hand and player.prize:
            actions.append(UseItemAction(player.id, self))
        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseItemAction):
            player = current_player(state)
            move_cards(self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state)
            # 从奖赏卡中选1张基础宝可梦(简化:从牌库选)
            basics = [c for c in player.prize if c.superType == SuperType.POKEMON and hasattr(c, "stage") and c.stage.value == "BASIC"]
            if basics:
                tips = _t("item.hisuian_heavy_ball")
                actions = choose_card_actions(player.id, player.id, 0, 1, basics, tips=tips, source=self)
                chosen = yield from reduce_choose_card_actions(actions, state)
                if chosen:
                    c = chosen[0]
                    if c in player.prize:
                        player.prize.remove(c)
                        player.hand.append(c)
