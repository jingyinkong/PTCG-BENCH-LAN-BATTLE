"""Counter Catcher - CIN 091"""
from ptcg.core.action import UseItemAction, choose_card_actions
from ptcg.core.card import ItemCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import current_player, move_cards, opponent_player
from ptcg.i18n import t as _t


class CIN091CounterCatcher(ItemCard):
    """Counter Catcher - Item. When behind on prizes, switch opponent's Active with Bench."""
    def __init__(self):
        super().__init__()
        self.set_name = "CIN"
        self.number = "091"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "反击捕捉器"
        self.cardType = CardType.NONE
        self.text = "这张卡牌，只有在自己的剩余奖赏卡张数，比对手的剩余奖赏卡张数多时才可使用。选择对手的1只备战宝可梦，将其与战斗宝可梦互换。"

    def get_actions(self, state):
        actions = []
        player = current_player(state)
        opponent = opponent_player(state)
        if self in player.hand and len(player.prize) > len(opponent.prize) and opponent.bench:
            actions.append(UseItemAction(player.id, self))
        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseItemAction):
            player = current_player(state)
            opponent = opponent_player(state)
            move_cards(self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state)
            tips = _t("supporter.counter_catcher")
            actions = choose_card_actions(
                player.id, opponent.id, 1, 1,
                list(opponent.bench), tips=tips, source=self
            )
            chosen = yield from reduce_choose_card_actions(actions, state)
            if chosen and opponent.active:
                old_active = opponent.active[0]
                new_active = chosen[0]
                if new_active in opponent.bench:
                    move_cards(old_active, (opponent.id, CardPosition.ACTIVE), (opponent.id, CardPosition.BENCH), state)
                    move_cards(new_active, (opponent.id, CardPosition.BENCH), (opponent.id, CardPosition.ACTIVE), state)
