from ptcg.core.action import UseSupporterAction, choose_card_actions
from ptcg.core.card import SupporterCard
from ptcg.core.enums import CardPosition, CardType, SuperType, TrainerType
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import current_player, move_cards, shuffle_cards
from ptcg.i18n import t as _t


class OBF186Arven(SupporterCard):
    def __init__(self):
        super().__init__()
        self.set_name = "OBF"
        self.number = "186"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "派帕"
        self.cardType = CardType.NONE
        self.text = (
            "Search your deck for an Item card and a Pokémon Tool card, reveal them, "
            "and put them into your hand. Then, shuffle your deck."
        )

    def get_actions(self, state):
        actions = []
        if not current_player(state).supporterPlayedTurn:
            actions.extend([UseSupporterAction(state.turn, self)])

        return actions

    def reduce_action(self, action, state):
        current_player(state).supporterPlayedTurn = True

        player = current_player(state)
        item_cards = [
            card
            for card in player.left
            if card.superType == SuperType.TRAINER and card.trainerType == TrainerType.ITEM
        ]
        tool_cards = [
            card
            for card in player.left
            if card.superType == SuperType.TRAINER and card.trainerType == TrainerType.TOOL
        ]

        if isinstance(action, UseSupporterAction):
            # discard self
            move_cards(
                self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state
            )

            tips = _t("supporter.arven.item")
            actions = choose_card_actions(
                player.id, player.id, 0, 1, item_cards, tips=tips, source=self
            )
            chosen_card = yield from reduce_choose_card_actions(actions, state)
            if all(card in player.left for card in chosen_card):
                move_cards(
                    chosen_card,
                    (player.id, CardPosition.LEFT),
                    (player.id, CardPosition.HAND),
                    state,
                )
            else:
                raise ValueError(f"Invalid action: {action}")

            tips = _t("supporter.arven.tool")
            actions = choose_card_actions(
                player.id, player.id, 0, 1, tool_cards, tips=tips, source=self
            )
            chosen_card = yield from reduce_choose_card_actions(actions, state)
            if all(card in player.left for card in chosen_card):
                move_cards(
                    chosen_card,
                    (player.id, CardPosition.LEFT),
                    (player.id, CardPosition.HAND),
                    state,
                )
            else:
                raise ValueError(f"Invalid action: {action}")

            shuffle_cards(player.left)
