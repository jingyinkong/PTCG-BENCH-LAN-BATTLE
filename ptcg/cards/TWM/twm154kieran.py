"""Kieran - TWM 154"""
from ptcg.core.action import UseSupporterAction
from ptcg.core.card import SupporterCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class TWM154Kieran(SupporterCard):
    """Kieran - Supporter. Switch your Active Pokémon, or during this turn
    attacks do +30 more damage. (Switch effect implemented.)"""
    def __init__(self):
        super().__init__()
        self.set_name = "TWM"
        self.number = "154"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "吉雉"
        self.cardType = CardType.NONE
        self.text = "选择1个效果:将自己的战斗宝可梦与备战宝可梦互换;或在下一个对手的回合结束前，自己的宝可梦使出的招式，对对手战斗宝可梦造成的伤害「+30」点。"

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
            # 默认选择效果1: 换位
            if player.active and player.bench:
                old_active = player.active[0]
                new_active = player.bench[0]
                move_cards(old_active, (player.id, CardPosition.ACTIVE), (player.id, CardPosition.BENCH), state)
                move_cards(new_active, (player.id, CardPosition.BENCH), (player.id, CardPosition.ACTIVE), state)
            player.supporterPlayedTurn = True
