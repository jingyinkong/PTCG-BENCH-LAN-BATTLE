"""深钵镇 - PAL 171"""
from ptcg.core.action import PutStadiumAction, DiscardStadiumAction
from ptcg.core.card import StadiumCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class PAL171Artazon(StadiumCard):
    """深钵镇 - 场地卡。"""
    def __init__(self):
        super().__init__()
        self.set_name = "PAL"
        self.number = "171"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "深钵镇"
        self.cardType = CardType.NONE
        self.text = "双方玩家，每次在自己的回合有1次机会，可选择自己牌库中的1张【基础】宝可梦（除「拥有规则的宝可梦」外），放于备战区。并重洗牌库。"

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
