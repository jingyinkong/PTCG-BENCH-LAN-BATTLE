"""Precious Trolley - SSP 185"""
from ptcg.core.action import UseItemAction
from ptcg.core.card import ItemCard
from ptcg.core.enums import CardPosition, CardType, Stage, SuperType
from ptcg.utils.utils import current_player, move_cards, shuffle_cards


class SSP185PreciousTrolley(ItemCard):
    """Precious Trolley - Item. Search deck for any number of Basic Pokémon and put them on Bench."""
    def __init__(self):
        super().__init__()
        self.set_name = "SSP"
        self.number = "185"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "贵重推车"
        self.cardType = CardType.NONE
        self.text = "选择自己牌库中任意数量的基础宝可梦，放于备战区。并重洗牌库。"

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
            basics = [c for c in player.left if c.superType == SuperType.POKEMON and c.stage == Stage.BASIC]
            bench_slots = 5 - len(player.bench)
            for i in range(min(bench_slots, len(basics))):
                if basics[i] in player.left:
                    move_cards(basics[i], (player.id, CardPosition.LEFT), (player.id, CardPosition.BENCH), state)
            shuffle_cards(player.left)
