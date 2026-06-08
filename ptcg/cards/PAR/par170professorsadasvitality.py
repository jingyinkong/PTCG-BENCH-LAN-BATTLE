"""Professor Sada\'s Vitality - PAR 170"""
from ptcg.core.action import UseSupporterAction, choose_card_actions
from ptcg.core.card import SupporterCard
from ptcg.core.enums import CardPosition, CardType, EnergyType, SuperType
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import current_player, move_cards
from ptcg.i18n import t as _t


class PAR170ProfessorSadasVitality(SupporterCard):
    """Professor Sada\'s Vitality - Supporter. Attach 1 basic Energy from discard to up to 2 Ancient Pokémon, then draw 3."""
    def __init__(self):
        super().__init__()
        self.set_name = "PAR"
        self.number = "170"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "奥琳博士的气魄"
        self.cardType = CardType.NONE
        self.text = "选择自己最多2只「古代」宝可梦，各附着1张弃牌区中的基本能量。然后，从自己牌库上方抽取3张卡牌。"

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
            # 从弃牌区选最多2张基本能量，附着于备战宝可梦
            basic_energies = [c for c in player.discard if c.superType == SuperType.ENERGY and c.energyType == EnergyType.BASIC]
            if basic_energies and player.bench:
                tips = _t("supporter.professor_sadas_vitality")
                actions = choose_card_actions(player.id, player.id, 0, min(2, len(basic_energies)), basic_energies, tips=tips, source=self)
                chosen = yield from reduce_choose_card_actions(actions, state)
                if chosen:
                    for energy in chosen[:2]:
                        if energy in player.discard and player.bench:
                            move_cards(energy, (player.id, CardPosition.DISCARD), (player.id, CardPosition.HAND), state)
            # 抽3张
            for _ in range(min(3, len(player.left))):
                move_cards(player.left[0], (player.id, CardPosition.LEFT), (player.id, CardPosition.HAND), state)
            player.supporterPlayedTurn = True
