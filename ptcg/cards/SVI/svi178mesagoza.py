"""Mesagoza - SVI 178"""
from ptcg.core.action import PutStadiumAction, DiscardStadiumAction
from ptcg.core.card import StadiumCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class SVI178Mesagoza(StadiumCard):
    """Mesagoza - Stadium."""
    def __init__(self):
        super().__init__()
        self.set_name = "SVI"
        self.number = "178"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "桌台市"
        self.cardType = CardType.NONE
        self.text = "双方玩家，每次在自己的回合有1次机会，可抛掷1次硬币。如果为正面，则选择自己牌库中的1张宝可梦，在给对手看过之后，加入手牌。并重洗牌库。"

    def get_actions(self, state):
        actions = []
        player = current_player(state)
        if not player.stadiumPlayedTurn and self in player.hand:
            actions.append(PutStadiumAction(player.id, self))
        return actions

    def reduce_action(self, action, state):
        player = current_player(state)
        if isinstance(action, PutStadiumAction):
            if state.stadium:
                old = state.stadium[0]
                try:
                    r = old.reduce_action(DiscardStadiumAction(old.playedFrom, old), state)
                    if r is not None:
                        yield from r
                except StopIteration:
                    pass
            self.playedFrom = player.id
            player.stadiumPlayedTurn = True
            move_cards(action.source, (player.id, CardPosition.HAND), (None, CardPosition.STADIUM), state)
