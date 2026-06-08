from ptcg.core.action import UseItemAction, choose_card_actions
from ptcg.core.card import ItemCard
from ptcg.core.enums import CardPosition, CardType, EnergyType, SuperType
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import current_player, move_cards
from ptcg.i18n import t as _t


class SFA061NightStretcher(ItemCard):
    def __init__(self):
        super().__init__()
        self.set_name = "SFA"
        self.number = "061"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "夜间担架"
        self.cardType = CardType.NONE
        self.text = "Put a Pokémon or a Basic Energy card from your discard pile into your hand."

    def get_actions(self, state):
        player = current_player(state)
        candidates = [
            c
            for c in player.discard
            if c.superType == SuperType.POKEMON
            or (c.superType == SuperType.ENERGY and c.energyType == EnergyType.BASIC)
        ]
        if candidates:
            return [UseItemAction(state.turn, self)]
        return []

    def reduce_action(self, action, state):
        if isinstance(action, UseItemAction):
            player = current_player(state)

            move_cards(
                self,
                (player.id, CardPosition.HAND),
                (player.id, CardPosition.DISCARD),
                state,
            )

            candidates = [
                c
                for c in player.discard
                if c.superType == SuperType.POKEMON
                or (c.superType == SuperType.ENERGY and c.energyType == EnergyType.BASIC)
            ]

            if candidates:
                tips = _t("item.night_stretcher")
                actions = choose_card_actions(
                    player.id, player.id, 1, 1, candidates, tips=tips, source=self
                )
                chosen = yield from reduce_choose_card_actions(actions, state)

                if chosen:
                    move_cards(
                        chosen[0],
                        (player.id, CardPosition.DISCARD),
                        (player.id, CardPosition.HAND),
                        state,
                    )
