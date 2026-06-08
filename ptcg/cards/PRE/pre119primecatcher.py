"""Prime Catcher - PRE 119"""
from ptcg.core.action import UseItemAction, choose_card_actions
from ptcg.core.card import ItemCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import current_player, move_cards, opponent_player
from ptcg.i18n import t as _t


class PRE119PrimeCatcher(ItemCard):
    """Prime Catcher - Item. Switch opponent's Active with 1 Benched Pokémon."""
    def __init__(self):
        super().__init__()
        self.set_name = "PRE"
        self.number = "119"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "高级捕捉器"
        self.cardType = CardType.NONE
        self.text = "选择对手的1只备战宝可梦，将其与战斗宝可梦互换。"

    def get_actions(self, state):
        actions = []
        player = current_player(state)
        opponent = opponent_player(state)
        if self in player.hand and opponent.bench:
            actions.append(UseItemAction(player.id, self))
        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseItemAction):
            player = current_player(state)
            opponent = opponent_player(state)
            move_cards(self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state)
            tips = _t("tool.prime_catcher.choose_opponent_bench")
            actions = choose_card_actions(player.id, opponent.id, 1, 1, list(opponent.bench), tips=tips, source=self)
            chosen = yield from reduce_choose_card_actions(actions, state)
            if chosen and opponent.active:
                old = opponent.active[0]
                new = chosen[0]
                if new in opponent.bench:
                    move_cards(old, (opponent.id, CardPosition.ACTIVE), (opponent.id, CardPosition.BENCH), state)
                    move_cards(new, (opponent.id, CardPosition.BENCH), (opponent.id, CardPosition.ACTIVE), state)
