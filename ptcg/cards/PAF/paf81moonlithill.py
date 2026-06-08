"""Moonlit Hill - PAF 081"""
from ptcg.core.action import PutStadiumAction, DiscardStadiumAction
from ptcg.core.card import StadiumCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class PAF081MoonlitHill(StadiumCard):
    """Moonlit Hill - Stadium."""
    def __init__(self):
        super().__init__()
        self.set_name = "PAF"
        self.number = "081"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "月光之丘"
        self.cardType = CardType.NONE
        self.text = "双方玩家，每次在自己的回合有1次机会，如果将自己手牌中的1张「基本【超】能量」放于弃牌区的话，则可将自己所有宝可梦的HP，各回复「30」。"

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
