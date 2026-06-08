"""Irida - ASR 147"""
from ptcg.core.action import UseSupporterAction, choose_card_actions
from ptcg.core.card import SupporterCard
from ptcg.core.enums import CardPosition, CardType, SuperType
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import current_player, move_cards, shuffle_cards
from ptcg.i18n import t as _t


class ASR147Irida(SupporterCard):
    """Irida - Supporter. Search deck for 1 Water Pokémon and 1 Item, reveal and add to hand."""
    def __init__(self):
        super().__init__()
        self.set_name = "ASR"
        self.number = "147"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "珠贝"
        self.cardType = CardType.NONE
        self.text = "选择自己牌库中的1只【水】宝可梦与1张物品卡，在给对手看过之后，加入手牌。并重洗牌库。"

    def get_actions(self, state):
        actions = []
        player = current_player(state)
        if not player.supporterPlayedTurn:
            actions.append(UseSupporterAction(state.turn, self))
        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseSupporterAction):
            player = current_player(state)
            move_cards(self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state)
            # 选1只水宝可梦
            water_pokemon = [c for c in player.left if c.superType == SuperType.POKEMON and hasattr(c, "cardType") and "WATER" in str(c.cardType)]
            if water_pokemon:
                tips = _t("supporter.irida.pokemon")
                actions = choose_card_actions(player.id, player.id, 0, 1, water_pokemon, tips=tips, source=self)
                chosen = yield from reduce_choose_card_actions(actions, state)
                if chosen and chosen[0] in player.left:
                    move_cards(chosen[0], (player.id, CardPosition.LEFT), (player.id, CardPosition.HAND), state)
            # 选1张物品
            items = [c for c in player.left if c.superType == SuperType.TRAINER and "ItemCard" in str(type(c))]
            if items:
                tips = _t("supporter.irida.item")
                actions = choose_card_actions(player.id, player.id, 0, 1, items, tips=tips, source=self)
                chosen = yield from reduce_choose_card_actions(actions, state)
                if chosen and chosen[0] in player.left:
                    move_cards(chosen[0], (player.id, CardPosition.LEFT), (player.id, CardPosition.HAND), state)
            shuffle_cards(player.left)
            player.supporterPlayedTurn = True
