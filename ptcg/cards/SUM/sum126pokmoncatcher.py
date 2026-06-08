"""Pokémon Catcher - SUM 126"""
from ptcg.core.action import UseItemAction, choose_card_actions
from ptcg.core.card import ItemCard
from ptcg.core.enums import CardPosition, CardType, Coin
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import current_player, flip_coin, move_cards, opponent_player
from ptcg.i18n import t as _t


class SUM126PokmonCatcher(ItemCard):
    """Pokémon Catcher - Item. Flip a coin. If heads, switch opponent's Active."""
    def __init__(self):
        super().__init__()
        self.set_name = "SUM"
        self.number = "126"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "宝可梦捕捉器"
        self.cardType = CardType.NONE
        self.text = "抛掷1次硬币。若为正面，选择对手的1只备战宝可梦，将其与战斗宝可梦互换。"

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
            if flip_coin(state) == Coin.HEAD and opponent.active and opponent.bench:
                tips = _t("item.pokemon_catcher")
                actions = choose_card_actions(player.id, opponent.id, 1, 1, list(opponent.bench), tips=tips, source=self)
                chosen = yield from reduce_choose_card_actions(actions, state)
                if chosen:
                    old = opponent.active[0]
                    new = chosen[0]
                    if new in opponent.bench:
                        move_cards(old, (opponent.id, CardPosition.ACTIVE), (opponent.id, CardPosition.BENCH), state)
                        move_cards(new, (opponent.id, CardPosition.BENCH), (opponent.id, CardPosition.ACTIVE), state)
