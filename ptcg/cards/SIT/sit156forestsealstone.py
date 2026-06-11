"""森林封印石 - SIT 156"""
from ptcg.core.ability import PassiveAbility
from ptcg.core.action import UseItemAction
from ptcg.core.card import ToolCard
from ptcg.core.enums import AbilityTrigger, AbilityType, CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class SIT156ForestSealStone(ToolCard):
    """森林封印石 - 宝可梦道具卡。"""
    def __init__(self):
        super().__init__()
        self.set_name = "SIT"
        self.number = "156"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "森林封印石"
        self.cardType = CardType.NONE
        self.text = "身上放有这张卡牌的「宝可梦V」，可以使用这个【VSTAR】力量。   [特性] 星耀炼金术 在自己的回合可以使用。选择自己牌库中任意1张卡牌，加入手牌。并重洗牌库。[对战中，己方的【VSTAR】力量只能使用1次。]"

        self.ability = [
            PassiveAbility(
                {
                    "name": "Star Alchemy",
                    "abilityType": AbilityType.PASSIVE_ABILITY,
                    "abilityTrigger": AbilityTrigger.ATTACKING,
                    "text": "During your turn, you may search your deck for any 1 card and put it into your hand. Then, shuffle your deck.",
                }
            )
        ]
        self.hasAttached = False
        self.attachedTo = None

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
            yield None
