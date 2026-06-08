"""Regidrago V - SIT 135"""
from ptcg.core.action import AttackAction, AttachEnergyAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import CardPosition, CardType, EnergyType, PokemonPosition, PokemonRule, PokemonType, Stage, SuperType
from ptcg.core.reducer import reduce_attack_action, reduce_attach_energy_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import auto_end_turn, check_energy, current_player, opponent_active
from ptcg.i18n import t as _t


class SIT135RegidragoV(PokemonCard):
    """Regidrago V - BASIC Pokemon. HP: 220.
    Attack: Sky's Roar - Discard top 3 cards of deck, attach any Energy among them."""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "SIT"; self.number = "135"; self.id = f"{self.set_name}-{self.number}"
        self.name = "雷吉铎拉戈V"; self.hp = 220
        self.pokemonType = PokemonType.V; self.pokemonRule = PokemonRule.NONE; self.stage = Stage.BASIC
        self.cardType = CardType.DRAGON
        self.retreat = [CardType.COLORLESS]*3; self.weakness = []; self.resistance = []
        self.evolveFrom = []; self.prize = 2
        self.energy = []; self.attachment = []; self.evolved = []
        self.attacks = [
            Attack({"name": "天之呐喊","damage": 0,"cost": [CardType.GRASS],"text": "将自己牌库上方3张卡牌放于弃牌区，将其中所有能量，附着于这只宝可梦身上。"}),
            Attack({"name": "巨龙镭射","damage": 130,"cost": [CardType.GRASS,CardType.FIRE,CardType.COLORLESS],"text": "给对手的1只备战宝可梦，也造成30点伤害。"})
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
            if action.attack.name == "天之呐喊":
                # 弃牌库顶3张，附着其中所有能量
                mill_count = min(3, len(player.left))
                milled = [player.left[0] for _ in range(mill_count)]
                for c in milled:
                    if c in player.left:
                        from ptcg.utils.utils import move_cards
                        move_cards(c, (player.id, CardPosition.LEFT), (player.id, CardPosition.DISCARD), state)
                for c in milled:
                    if c in player.discard and c.superType == SuperType.ENERGY:
                        player.discard.remove(c)
                        reduce_attach_energy_action(AttachEnergyAction(player.id, c, self), state, is_ability=True)
                auto_end_turn(state)
            elif action.attack.name == "巨龙镭射":
                yield from reduce_attack_action(action, state)
                # 对1只备战宝可梦造成30伤害
                from ptcg.core.action import EffectAction, choose_card_actions
                from ptcg.core.effect import Effect
                from ptcg.core.reducer import reduce_choose_card_actions as rc, reduce_effect_action
                from ptcg.utils.utils import opponent_bench, opponent_player
                bench = opponent_player(state).bench
                if bench:
                    tips = _t("attack.regidrago_v.dragon_laser")
                    act = choose_card_actions(player.id, player.id, 1, 1, list(bench), tips=tips, source=self)
                    chosen = yield from rc(act, state)
                    if chosen:
                        effect = Effect(3)  # 3 damage counters = 30 HP
                        yield from reduce_effect_action(EffectAction(player.id, self, effect, chosen[0]), state)
                auto_end_turn(state)
            else:
                yield from reduce_attack_action(action, state)
