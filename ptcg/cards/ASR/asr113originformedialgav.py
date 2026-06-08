"""Origin Forme Dialga V - ASR 113"""
from ptcg.core.action import AttackAction, AttachEnergyAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction, choose_card_actions
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import CardPosition, CardType, EnergyType, PokemonPosition, PokemonRule, PokemonType, Stage, SuperType
from ptcg.core.reducer import reduce_attack_action, reduce_attach_energy_action, reduce_choose_card_actions, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import auto_end_turn, check_energy, current_player, opponent_active
from ptcg.i18n import t as _t


class ASR113OriginFormeDialgaV(PokemonCard):
    """Origin Forme Dialga V - BASIC Pokemon. HP: 220."""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "ASR"; self.number = "113"; self.id = f"{self.set_name}-{self.number}"
        self.name = "起源帝牙卢卡V"; self.hp = 220
        self.pokemonType = PokemonType.V; self.pokemonRule = PokemonRule.NONE; self.stage = Stage.BASIC
        self.cardType = CardType.METAL
        self.retreat = [CardType.COLORLESS]*2; self.weakness = [CardType.FIRE]; self.resistance = [CardType.GRASS]
        self.evolveFrom = []; self.prize = 2
        self.energy = []; self.attachment = []; self.evolved = []
        self.attacks = [
            Attack({"name": "金属涂层","damage": 0,"cost": [CardType.COLORLESS],"text": "选择自己弃牌区中最多2张【钢】能量，附着于这只宝可梦身上。"}),
            Attack({"name": "时间断绝","damage": 180,"cost": [CardType.METAL,CardType.METAL,CardType.METAL,CardType.COLORLESS],"text": ""})
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
            if action.attack.name == "金属涂层":
                metal_energies = [c for c in player.discard if c.superType == SuperType.ENERGY and c.energyType == EnergyType.BASIC and hasattr(c,'provides') and CardType.METAL in c.provides]
                if metal_energies:
                    max_e = min(2, len(metal_energies))
                    tips = _t("ability.origin_dialga_v.metal_coating")
                    energy_actions = choose_card_actions(player.id, player.id, 0, max_e, metal_energies, tips=tips, source=self)
                    chosen = yield from reduce_choose_card_actions(energy_actions, state)
                    if chosen:
                        for ec in chosen:
                            if ec in player.discard:
                                player.discard.remove(ec)
                            reduce_attach_energy_action(AttachEnergyAction(player.id, ec, self), state, is_ability=True)
                auto_end_turn(state)
            elif action.attack.name == "时间断绝":
                yield from reduce_attack_action(action, state)
