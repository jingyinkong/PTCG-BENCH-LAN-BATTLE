from ptcg.core.ability import ActiveAbility
from ptcg.core.action import (
    AttackAction, PlayPokemonAction, RetreatAction, UseAbilityAction, choose_card_actions
)
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import (
    AbilityType,
    CardPosition,
    CardType,
    PokemonPosition,
    PokemonRule,
    PokemonType,
    Stage,
    SuperType,
    TrainerType
)
from ptcg.core.reducer import reduce_attack_action, reduce_choose_card_actions, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.i18n import t as _t
from ptcg.utils.utils import (
    auto_end_turn, check_energy, current_player, move_cards, opponent_active
)


class CRZ045RotomV(PokemonCard):
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "CRZ"
        self.number = "045"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "切割洛托姆"
        self.hp = 190
        self.pokemonType = PokemonType.V
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.LIGHTNING
        self.retreat = [CardType.COLORLESS]
        self.weakness = [CardType.FIGHTING]
        self.resistance = []
        self.prize = 2

        self.energy = []
        self.attachment = []

        self.attacks = [
            Attack(
                {
                    "name": "Scrap Short",
                    "damage": 40,
                    "cost": [CardType.LIGHTNING, CardType.LIGHTNING],
                    "text": "Put any number of Pokémon Tool cards from your discard pile in the Lost Zone. "
                    "This attack does 40 more damage for each card you put in the Lost Zone in this way.",
                }
            )
        ]

        self.ability = [
            ActiveAbility(
                {
                    "name": "Instant Charge",
                    "abilityType": AbilityType.ACTIVE_ABILITY,
                    "onceUsedPerTurn": False,
                    "text": "Once during your turn, you may draw 3 cards. If you use this Ability, your turn ends.",
                }
            )
        ]

    def get_actions(self, state):
        actions = []
        targets = opponent_active(state)

        if self.position == PokemonPosition.ACTIVE:
            for attack in self.attacks:
                if check_energy(attack.cost, self.energy):
                    actions.extend(
                        [AttackAction(state.turn, self, attack, target) for target in targets]
                    )

        for ability in self.ability:
            actions.extend([UseAbilityAction(state.turn, self, ability)])

        return actions

    def reduce_action(self, action, state):
        if isinstance(action, PlayPokemonAction):
            reduce_play_pokemon_action(action, state)

        elif isinstance(action, AttackAction):
            player = current_player(state)
            cards = [
                card
                for card in player.discard
                if card.superType == SuperType.TRAINER and card.trainerType == TrainerType.TOOL
            ]
            tips = _t("attack.rotom_v.scrap_short")
            actions = choose_card_actions(
                player.id, player.id, 0, len(cards), cards, tips=tips, source=self
            )
            chosen_card = yield from reduce_choose_card_actions(actions, state)
            if all(card in player.discard for card in chosen_card):
                move_cards(
                    chosen_card,
                    (player.id, CardPosition.DISCARD),
                    (player.id, CardPosition.LOSTZONE),
                    state,
                )
                action.attack.damage = 40 + 40 * len(chosen_card)
                yield from reduce_attack_action(action, state)
            else:
                raise ValueError(f"Invalid action: {action}")

        elif isinstance(action, UseAbilityAction):
            player = current_player(state)
            draw_cards = player.left[:3]
            move_cards(
                draw_cards, (player.id, CardPosition.LEFT), (player.id, CardPosition.HAND), state
            )

            auto_end_turn(state)

        elif isinstance(action, RetreatAction):
            yield from reduce_retreat_action(action, state)

        else:
            raise ValueError(f"Invalid action: {action}")
