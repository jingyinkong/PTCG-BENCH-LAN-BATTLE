"""Raichu V - BRS 045"""
from ptcg.core.action import AttackAction, AttachEnergyAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction, choose_card_actions
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import CardPosition, CardType, EnergyType, PokemonPosition, PokemonRule, PokemonType, Stage, SuperType
from ptcg.core.reducer import reduce_attack_action, reduce_attach_energy_action, reduce_choose_card_actions, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import auto_end_turn, check_energy, current_player, opponent_active, shuffle_cards
from ptcg.i18n import t as _t


class BRS045RaichuV(PokemonCard):
    """Raichu V - BASIC Pokemon. HP: 200."""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "BRS"; self.number = "045"; self.id = f"{self.set_name}-{self.number}"
        self.name = "雷丘V"; self.hp = 200
        self.pokemonType = PokemonType.V; self.pokemonRule = PokemonRule.NONE; self.stage = Stage.BASIC
        self.cardType = CardType.LIGHTNING
        self.retreat = [CardType.COLORLESS]; self.weakness = [CardType.FIGHTING]; self.resistance = []
        self.evolveFrom = []; self.prize = 2
        self.energy = []; self.attachment = []; self.evolved = []
        self.attacks = [
            Attack({"name": "快速充能","damage": 0,"cost": [CardType.COLORLESS],"text": "即使是先攻最初回合也可使用。选择牌库中1张雷能量，附着于这只宝可梦身上。"}),
            Attack({"name": "强劲电光","damage": 0,"cost": [CardType.LIGHTNING,CardType.LIGHTNING],"text": "将附着于场上宝可梦身上任意数量的雷能量放于弃牌区，造成其张数x60伤害。"})
        ]

    def get_actions(self, state):
        actions = []
        if self.position == PokemonPosition.ACTIVE:
            for attack in self.attacks:
                if check_energy(attack.cost, self.energy):
                    targets = opponent_active(state)
                    if targets:
                        actions.append(AttackAction(state.turn, self, attack, targets[0]))
                        break
        return actions

    def reduce_action(self, action, state):
        if isinstance(action, PlayPokemonAction): reduce_play_pokemon_action(action, state)
        elif isinstance(action, EvolvePokemonAction): reduce_evolve_pokemon_action(action, state)
        elif isinstance(action, RetreatAction): yield from reduce_retreat_action(action, state)
        elif isinstance(action, AttackAction):
            player = current_player(state)
            if action.attack.name == "快速充能":
                # 从牌库搜1张雷能量附着
                lightning_energies = [c for c in player.left if c.superType == SuperType.ENERGY and c.energyType == EnergyType.BASIC and hasattr(c,'provides') and CardType.LIGHTNING in c.provides]
                if lightning_energies:
                    tips = _t("attack.raichu_v.fast_charge")
                    acts = choose_card_actions(player.id, player.id, 1, 1, lightning_energies, tips=tips, source=self)
                    chosen = yield from reduce_choose_card_actions(acts, state)
                    if chosen and chosen[0] in player.left:
                        from ptcg.utils.utils import move_cards
                        move_cards(chosen[0], (player.id, CardPosition.LEFT), (player.id, CardPosition.HAND), state)
                        reduce_attach_energy_action(AttachEnergyAction(player.id, chosen[0], self), state, is_ability=True)
                    shuffle_cards(player.left)
                auto_end_turn(state)
            elif action.attack.name == "强劲电光":
                # 选能量弃掉,伤害=弃掉数x60
                energy_options = [e for e in self.energy if e == CardType.LIGHTNING]
                if energy_options:
                    from ptcg.core.action import choose_card_actions as cc
                    tips = _t("attack.raichu_v.dynamic_spark")
                    acts = cc(player.id, player.id, 0, len(energy_options), energy_options, tips=tips, source=self)
                    chosen = yield from reduce_choose_card_actions(acts, state)
                    if chosen:
                        for e in chosen:
                            if e in self.energy: self.energy.remove(e)
                        action.attack.damage = len(chosen) * 60
                yield from reduce_attack_action(action, state)
                auto_end_turn(state)
            else:
                yield from reduce_attack_action(action, state)
