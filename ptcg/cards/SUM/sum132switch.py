"""宝可梦交替 - 道具卡。将自己的战斗宝可梦与备战宝可梦互换。"""
from ptcg.core.action import UseItemAction, choose_card_actions
from ptcg.core.card import ItemCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import current_player, move_cards, switch_pokemon
from ptcg.i18n import t as _t


class SUM132Switch(ItemCard):
    """宝可梦交替 - SUM 132"""
    def __init__(self):
        super().__init__()
        self.set_name = "SUM"
        self.number = "132"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "宝可梦交替"
        self.cardType = CardType.NONE
        self.text = "将自己的战斗宝可梦与备战宝可梦互换。"

    def get_actions(self, state):
        player = current_player(state)
        actions = []
        if len(player.bench) > 0:
            actions.append(UseItemAction(state.turn, self))
        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseItemAction):
            player = current_player(state)
            move_cards(self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state)
            tips = _t("item.switch")
            actions = choose_card_actions(player.id, player.id, 1, 1, player.bench, tips=tips, source=self)
            chosen = yield from reduce_choose_card_actions(actions, state)
            if chosen:
                switch_pokemon(chosen[0], player.active[0], player)
