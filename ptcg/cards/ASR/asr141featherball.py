"""Feather Ball - ASR 141"""
from ptcg.core.action import UseItemAction, choose_card_actions
from ptcg.core.card import ItemCard
from ptcg.core.enums import CardPosition, CardType, SuperType
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import current_player, move_cards, shuffle_cards
from ptcg.i18n import t as _t


class ASR141FeatherBall(ItemCard):
    """Feather Ball - Item. Search deck for a Pokémon with no Retreat Cost, reveal and add to hand."""
    def __init__(self):
        super().__init__()
        self.set_name = "ASR"
        self.number = "141"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "羽毛球"
        self.cardType = CardType.NONE
        self.text = "选择自己牌库中的1只「撤退」费用为0的宝可梦，在给对手看过之后，加入手牌。并重洗牌库。"

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
            no_retreat = [c for c in player.left if c.superType == SuperType.POKEMON and hasattr(c, "retreat") and len(c.retreat) == 0]
            if no_retreat:
                tips = _t("item.feather_ball")
                actions = choose_card_actions(player.id, player.id, 0, 1, no_retreat, tips=tips, source=self)
                chosen = yield from reduce_choose_card_actions(actions, state)
                if chosen and chosen[0] in player.left:
                    move_cards(chosen[0], (player.id, CardPosition.LEFT), (player.id, CardPosition.HAND), state)
            shuffle_cards(player.left)
