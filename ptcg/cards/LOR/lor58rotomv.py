"""Rotom V - LOR 058"""
from ptcg.core.ability import ActiveAbility
from ptcg.core.action import (
    AttackAction, PlayPokemonAction, RetreatAction, UseAbilityAction, choose_card_actions
)
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import (
    AbilityType, CardPosition, CardType, PokemonPosition, PokemonRule, PokemonType, Stage, SuperType
)
from ptcg.core.reducer import (
    reduce_attack_action, reduce_choose_card_actions, reduce_play_pokemon_action, reduce_retreat_action
)
from ptcg.i18n import t as _t
from ptcg.utils.utils import (
    current_player, move_cards, shuffle_cards
)


class LOR058RotomV(PokemonCard):
    """Rotom V - BASIC Pokemon. HP: 190. Ability: Instant Charge."""

    def __init__(self) -> None:
        super().__init__()
        self.set_name = "LOR"
        self.number = "058"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "洛托姆V"
        self.hp = 190
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.LIGHTNING
        self.retreat = [CardType.COLORLESS]
        self.weakness = [CardType.FIGHTING]
        self.resistance = []
        self.evolveFrom = []
        self.prize = 2
        self.energy = []
        self.attachment = []
        self.evolved = []

        self.attacks = [
            Attack({
                "name": "废品短路",
                "damage": 40,
                "cost": [CardType.LIGHTNING, CardType.LIGHTNING],
                "text": "将自己弃牌区中任意数量的「宝可梦道具」放于放逐区，追加造成其张数x40点伤害。",
            })
        ]

        self.ability = [
            ActiveAbility({
                "name": "Instant Charge",
                "abilityType": AbilityType.ACTIVE_ABILITY,
                "onceUsedPerTurn": True,
                "text": "在自己的回合，从手牌将这张卡放置于备战区时，可使用1次。"
                       "从自己的牌库选择最多2张基本雷能量，附着于这只宝可梦身上。并重洗牌库。",
            })
        ]

    def get_actions(self, state):
        actions = []

        if self.position == PokemonPosition.ACTIVE:
            for attack in self.attacks:
                if attack.cost and all(
                    any(ec == c for c in self.energy) for ec in attack.cost
                ):
                    from ptcg.utils.utils import opponent_active
                    targets = opponent_active(state)
                    actions.extend(
                        [AttackAction(state.turn, self, attack, t) for t in targets]
                    )

        for ability in self.ability:
            actions.append(UseAbilityAction(state.turn, self, ability))

        return actions

    def reduce_action(self, action, state):
        if isinstance(action, PlayPokemonAction):
            reduce_play_pokemon_action(action, state)

        elif isinstance(action, AttackAction):
            player = current_player(state)
            cards = [
                card
                for card in player.discard
                if card.superType == SuperType.TRAINER and hasattr(card, 'trainerType')
                and getattr(card, 'trainerType', None) is not None
            ]
            if cards:
                tips = _t("attack.rotom_v.scrap_short")
                actions = choose_card_actions(
                    player.id, player.id, 0, len(cards), cards, tips=tips, source=self
                )
                chosen_card = yield from reduce_choose_card_actions(actions, state)
                if all(c in player.discard for c in chosen_card):
                    move_cards(
                        chosen_card,
                        (player.id, CardPosition.DISCARD),
                        (player.id, CardPosition.LOSTZONE),
                        state,
                    )
                    action.attack.damage = 40 + 40 * len(chosen_card)
            yield from reduce_attack_action(action, state)

        elif isinstance(action, UseAbilityAction):
            player = current_player(state)
            # Search deck for up to 2 basic Lightning Energy cards
            lightning_energy = [
                card for card in player.left
                if card.superType == SuperType.ENERGY
                and hasattr(card, 'cardType') and card.cardType == CardType.LIGHTNING
            ]
            if lightning_energy:
                tips = _t("ability.rotom_v.instant_charge")
                actions = choose_card_actions(
                    player.id, player.id, 0, min(2, len(lightning_energy)),
                    lightning_energy, tips=tips, source=self
                )
                chosen = yield from reduce_choose_card_actions(actions, state)
                if chosen:
                    move_cards(
                        chosen,
                        (player.id, CardPosition.LEFT),
                        (player.id, CardPosition.HAND),
                        state,
                    )
                    # Attach energy from hand to this Pokemon
                    for energy_card in chosen:
                        if energy_card in player.hand:
                            self.energy.append(energy_card.cardType)
                            player.hand.remove(energy_card)
                            self.attachment.append(energy_card)
            shuffle_cards(player.left)

        elif isinstance(action, RetreatAction):
            yield from reduce_retreat_action(action, state)

        else:
            raise ValueError(f"Invalid action: {action}")
