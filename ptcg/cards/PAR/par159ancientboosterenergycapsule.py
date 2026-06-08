"""Ancient Booster Energy Capsule - PAR 159"""
from ptcg.core.action import UseItemAction
from ptcg.core.card import ToolCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class PAR159AncientBoosterEnergyCapsule(ToolCard):
    """Ancient Booster Energy Capsule - Tool."""
    def __init__(self):
        super().__init__()
        self.set_name = "PAR"
        self.number = "159"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "驱劲能量 古代"
        self.cardType = CardType.NONE
        self.text = "身上放有这张卡牌的「古代」宝可梦，最大HP「+60」，那只宝可梦，不会陷入特殊状态，已经处于的特殊状态，也全部恢复。"

    def get_actions(self, state):
        actions = []
        player = current_player(state)
        actions.append(UseItemAction(player.id, self))
        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseItemAction):
            player = current_player(state)
            move_cards(self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state)
