"""Briar - PRE 100"""
from ptcg.core.action import UseSupporterAction
from ptcg.core.card import SupporterCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards, opponent_player


class PRE100Briar(SupporterCard):
    """Briar - Supporter. Usable when opponent has exactly 2 prizes.
    During this turn, attacks do +30 damage to opponent's Active (handled by state marker)."""
    def __init__(self):
        super().__init__()
        self.set_name = "PRE"
        self.number = "100"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "白蕾雅"
        self.cardType = CardType.NONE
        self.text = "只有对手剩余奖赏卡为2张时才可使用。在这个回合，自己的宝可梦使出的招式，对对手战斗宝可梦造成的伤害「+30」点。"

    def get_actions(self, state):
        actions = []
        player = current_player(state)
        opponent = opponent_player(state)
        if not player.supporterPlayedTurn and len(opponent.prize) == 2:
            actions.append(UseSupporterAction(state.turn, self))
        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseSupporterAction):
            player = current_player(state)
            move_cards(self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state)
            # 设置伤害加成标记(由引擎检查)
            player.attackBonusThisTurn = 30
            player.supporterPlayedTurn = True
