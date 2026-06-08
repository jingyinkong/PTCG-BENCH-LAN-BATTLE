"""Scoop Up Cyclone - PRE 128"""
from ptcg.core.action import UseItemAction, choose_card_actions
from ptcg.core.card import ItemCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import current_player, move_cards
from ptcg.i18n import t as _t


class PRE128ScoopUpCyclone(ItemCard):
    """Scoop Up Cyclone - Item. Return 1 of your Pokémon and all attached cards to hand."""
    def __init__(self):
        super().__init__()
        self.set_name = "PRE"
        self.number = "128"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "宝可梦旋风回收机"
        self.cardType = CardType.NONE
        self.text = "选择自己场上的1只宝可梦，将其与身上附加的卡牌，全部放回手牌。"

    def get_actions(self, state):
        actions = []
        player = current_player(state)
        if self in player.hand:
            actions.append(UseItemAction(player.id, self))
        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseItemAction):
            player = current_player(state)
            move_cards(self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state)
            field = list(player.bench)
            if field:
                tips = _t("item.scoop_up_cyclone")
                actions = choose_card_actions(player.id, player.id, 1, 1, field, tips=tips, source=self)
                chosen = yield from reduce_choose_card_actions(actions, state)
                if chosen:
                    pokemon = chosen[0]
                    # 清空能量(引擎以CardType存储)
                    pokemon.energy.clear()
                    for att in list(pokemon.attachment):
                        pokemon.attachment.remove(att); att.cardPosition = CardPosition.HAND; player.hand.append(att)
                    move_cards(pokemon, (player.id, CardPosition.BENCH), (player.id, CardPosition.HAND), state)
