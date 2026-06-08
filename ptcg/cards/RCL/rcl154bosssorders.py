"""老大的指令 - 支援者卡。将对手的1只备战宝可梦与其战斗宝可梦互换。"""
from ptcg.core.action import UseSupporterAction, choose_card_actions
from ptcg.core.card import SupporterCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import current_player, move_cards, opponent_player, switch_pokemon
from ptcg.i18n import t as _t


class RCL154BosssOrders(SupporterCard):
    """老大的指令 - RCL 154"""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "RCL"
        self.number = "154"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "老大的指令"
        self.cardType = CardType.NONE
        self.text = "将对手的1只备战宝可梦与其战斗宝可梦互换。"

    def get_actions(self, state):
        player = current_player(state)
        opponent = opponent_player(state)
        actions = []
        if not player.supporterPlayedTurn and len(opponent.bench) != 0:
            actions.extend([UseSupporterAction(state.turn, self)])
        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseSupporterAction):
            player = current_player(state)
            opponent = opponent_player(state)
            move_cards(self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state)
            tips = _t("supporter.bosss_orders")
            actions = choose_card_actions(player.id, opponent.id, 1, 1, opponent.bench, tips=tips, source=self)
            chosen_card = yield from reduce_choose_card_actions(actions, state)
            chosen_card = chosen_card[0]
            if chosen_card in opponent.bench:
                switch_pokemon(chosen_card, opponent.active[0], opponent)
            player.supporterPlayedTurn = True
