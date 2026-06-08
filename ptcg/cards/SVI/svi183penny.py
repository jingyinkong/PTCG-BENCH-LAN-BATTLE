"""Penny - SVI 183"""
from ptcg.core.action import UseSupporterAction, choose_card_actions
from ptcg.core.card import SupporterCard
from ptcg.core.enums import CardPosition, CardType, Stage
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import current_player, move_cards
from ptcg.i18n import t as _t


class SVI183Penny(SupporterCard):
    """Penny - Supporter. Return 1 Basic Pokémon and all attached cards to hand."""
    def __init__(self):
        super().__init__()
        self.set_name = "SVI"
        self.number = "183"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "皮拿"
        self.cardType = CardType.NONE
        self.text = "选择自己场上的1只基础宝可梦，将其与身上附加的卡牌，全部放回手牌。"

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
            # 选择1只基础宝可梦返回手牌
            field = list(player.bench)
            basics = [p for p in field if p.stage == Stage.BASIC]
            if basics:
                tips = _t("supporter.penny")
                actions = choose_card_actions(player.id, player.id, 1, 1, basics, tips=tips, source=self)
                chosen = yield from reduce_choose_card_actions(actions, state)
                if chosen:
                    pokemon = chosen[0]
                    # 清空能量(引擎以CardType存储,非Card对象)
                    pokemon.energy.clear()
                    for att in list(pokemon.attachment):
                        pokemon.attachment.remove(att)
                        att.cardPosition = CardPosition.HAND
                        player.hand.append(att)
                    move_cards(pokemon, (player.id, CardPosition.BENCH), (player.id, CardPosition.HAND), state)
            player.supporterPlayedTurn = True
