"""Energy Loto - GRI 122"""
from ptcg.core.action import UseItemAction, choose_card_actions
from ptcg.core.card import ItemCard
from ptcg.core.enums import CardPosition, CardType, EnergyType, SuperType
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import current_player, move_cards, shuffle_cards
from ptcg.i18n import t as _t


class GRI122EnergyLoto(ItemCard):
    """Energy Loto - Item. Look at top 7 cards, take 1 basic Energy, shuffle."""
    def __init__(self):
        super().__init__()
        self.set_name = "GRI"
        self.number = "122"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "能量抽出"
        self.cardType = CardType.NONE
        self.text = "查看自己牌库上方的7张卡牌，选择其中1张基本能量，在给对手看过之后，加入手牌。将剩余卡牌放回牌库并重洗。"

    def get_actions(self, state):
        actions = []
        player = current_player(state)
        if self in player.hand and len(player.left) >= 1:
            actions.append(UseItemAction(player.id, self))
        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseItemAction):
            player = current_player(state)
            move_cards(self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state)
            # 查看牌库顶7张，选1张基本能量
            look_count = min(7, len(player.left))
            looked = [player.left[i] for i in range(look_count)]
            basic_energies = [c for c in looked if c.superType == SuperType.ENERGY and c.energyType == EnergyType.BASIC]
            if basic_energies:
                tips = _t("item.energy_loto")
                actions = choose_card_actions(
                    player.id, player.id, 0, 1, basic_energies, tips=tips, source=self
                )
                chosen = yield from reduce_choose_card_actions(actions, state)
                if chosen:
                    for c in chosen:
                        if c in player.left:
                            move_cards(c, (player.id, CardPosition.LEFT), (player.id, CardPosition.HAND), state)
            shuffle_cards(player.left)
