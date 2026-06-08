"""Judge - FLI 108"""
from ptcg.core.action import UseSupporterAction
from ptcg.core.card import SupporterCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards, opponent_player, shuffle_cards


class FLI108Judge(SupporterCard):
    """Judge - Supporter. Both players shuffle hands into decks, draw 4."""
    def __init__(self):
        super().__init__()
        self.set_name = "FLI"
        self.number = "108"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "裁判"
        self.cardType = CardType.NONE
        self.text = "双方玩家，各将所有手牌放回牌库并重洗牌库。然后，各从牌库上方抽取4张卡牌。"

    def get_actions(self, state):
        actions = []
        player = current_player(state)
        if not player.supporterPlayedTurn:
            actions.append(UseSupporterAction(state.turn, self))
        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseSupporterAction):
            player = current_player(state)
            opponent = opponent_player(state)
            move_cards(self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state)
            # 双方手牌放回牌库并重洗
            for p in [player, opponent]:
                for card in list(p.hand):
                    move_cards(card, (p.id, CardPosition.HAND), (p.id, CardPosition.LEFT), state)
                shuffle_cards(p.left)
                for _ in range(min(4, len(p.left))):
                    move_cards(p.left[0], (p.id, CardPosition.LEFT), (p.id, CardPosition.HAND), state)
            player.supporterPlayedTurn = True
