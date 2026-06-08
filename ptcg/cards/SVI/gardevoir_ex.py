from ptcg.core.ability import PassiveAbility
from ptcg.core.action import (
    AttackAction, AttachEnergyAction, EffectAction, EvolvePokemonAction,
    UseAbilityAction, choose_card_actions
)
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.effect import Effect
from ptcg.core.enums import (
    AbilityType, CardPosition, CardType, EnergyType, PokemonPosition,
    PokemonRule, PokemonType, Stage, SuperType
)
from ptcg.core.reducer import (
    reduce_attack_action, reduce_attach_energy_action,
    reduce_choose_card_actions, reduce_effect_action,
    reduce_evolve_pokemon_action
)
from ptcg.i18n import t as _t
from ptcg.utils.utils import (
    check_energy, current_all_pokemon,
    current_player, opponent_active
)


class SVI086Gardevoirex(PokemonCard):
    """Gardevoir ex - STAGE 2 Pokemon. HP: 310.
    
    Ability: Psychic Embrace - Attach Basic Psychic Energy from discard
    to a Psychic Pokemon, then put 2 damage counters on it.
    """
    def __init__(self) -> None:
        super().__init__()
        self.name = "沙奈朵ex"
        self.set_name = "SVI"
        self.number = "086"
        self.id = f"{self.set_name}-{self.number}"
        self.hp = 310
        self.pokemonType = PokemonType.EX_LOWERCASE
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.STAGE_2
        self.cardType = CardType.PSYCHIC
        self.retreat = [CardType.COLORLESS, CardType.COLORLESS]
        self.weakness = [CardType.DARK]
        self.resistance = []
        self.prize = 2
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.evolveFrom = ["奇鲁莉安", "拉鲁拉丝"]
        self.attacks = [
            Attack({
                "name": "Miracle Force",
                "damage": 190,
                "cost": [CardType.PSYCHIC, CardType.PSYCHIC, CardType.COLORLESS],
                "text": "This Pokémon recovers from all Special Conditions.",
            })
        ]
        self.ability = [
            PassiveAbility({
                "name": "Psychic Embrace",
                "abilityType": AbilityType.PASSIVE_ABILITY,
                "abilityTrigger": AbilityType.ACTIVE_ABILITY,
                "onceUsedPerTurn": False,
                "text": "As often as you like during your turn, you may attach a Basic Psychic Energy card from your discard pile to 1 of your Psychic Pokémon. Put 2 damage counters on that Pokémon.",
            })
        ]

    def get_actions(self, state):
        actions = []
        player = current_player(state)

        if self.position == PokemonPosition.ACTIVE:
            for attack in self.attacks:
                if check_energy(attack.cost, self.energy):
                    targets = opponent_active(state)
                    if targets:
                        actions.append(AttackAction(state.turn, self, attack, targets[0]))

        # Psychic Embrace: always available when there's Psychic energy in discard
        psychic_in_discard = any(
            c.superType == SuperType.ENERGY and c.energyType == EnergyType.BASIC 
            and hasattr(c, 'provides') and CardType.PSYCHIC in c.provides
            for c in player.discard
        )
        if psychic_in_discard:
            for ability in self.ability:
                actions.append(UseAbilityAction(state.turn, self, ability))

        return actions

    def reduce_action(self, action, state):
        if isinstance(action, EvolvePokemonAction):
            reduce_evolve_pokemon_action(action, state)
        elif isinstance(action, AttackAction):
            yield from reduce_attack_action(action, state)
        elif isinstance(action, UseAbilityAction):
            yield from self._apply_psychic_embrace(action, state)

    def _apply_psychic_embrace(self, action, state):
        """Psychic Embrace: Attach Psychic energy from discard, add 2 damage counters."""
        player = current_player(state)

        # Step 1: Select basic Psychic energy from discard
        psychic_energies = [
            c for c in player.discard
            if c.superType == SuperType.ENERGY and c.energyType == EnergyType.BASIC
            and hasattr(c, 'provides') and CardType.PSYCHIC in c.provides
        ]
        if not psychic_energies:
            return

        tips = _t("ability.gardevoir_ex.psychic_embrace.choose_energy")
        energy_actions = choose_card_actions(
            player.id, player.id, 1, 1, psychic_energies, tips=tips, source=self
        )
        chosen_energy = yield from reduce_choose_card_actions(energy_actions, state)

        if not chosen_energy:
            return
        energy_card = chosen_energy[0]
        if energy_card not in player.discard:
            return

        # Step 2: Select a Psychic Pokemon as target
        all_my_pokemon = current_all_pokemon(state)
        psychic_targets = [
            p for p in all_my_pokemon
            if hasattr(p, 'cardType') and p.cardType == CardType.PSYCHIC
        ]
        if not psychic_targets:
            return

        tips = _t("ability.gardevoir_ex.psychic_embrace.choose_target")
        target_actions = choose_card_actions(
            player.id, player.id, 1, 1, psychic_targets, tips=tips, source=self
        )
        chosen_target = yield from reduce_choose_card_actions(target_actions, state)

        if not chosen_target:
            return
        target = chosen_target[0]

        # Step 3: 从弃牌区附着能量
        if energy_card in player.discard:
            from ptcg.utils.utils import move_cards as mc2
            mc2(energy_card, (player.id, CardPosition.DISCARD), (player.id, CardPosition.HAND), state)
        target.energy.extend(energy_card.provides)
        if not hasattr(target, 'attachment'):
            target.attachment = []
        target.attachment.append(energy_card)

        # Step 4: 放置2个伤害指示物(每个=10HP)
        effect = Effect(2)
        yield from reduce_effect_action(
            EffectAction(player.id, self, effect, target), state
        )
