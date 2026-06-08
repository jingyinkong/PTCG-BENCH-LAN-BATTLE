"""Duskull - PRE 035"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction, choose_card_actions
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import CardPosition, CardType, PokemonPosition, PokemonRule, PokemonType, Stage, SuperType
from ptcg.core.reducer import reduce_attack_action, reduce_choose_card_actions, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import auto_end_turn, check_energy, current_player, move_cards, opponent_active
from ptcg.i18n import t as _t


class PRE035Duskull(PokemonCard):
    """Duskull - BASIC Pokemon. HP: 60.
    Attack: Soul Ferry - Put up to 3 Duskull from discard to bench."""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "PRE"; self.number = "035"; self.id = f"{self.set_name}-{self.number}"
        self.name = "夜巡灵"; self.hp = 60
        self.pokemonType = PokemonType.NORMAL; self.pokemonRule = PokemonRule.NONE; self.stage = Stage.BASIC
        self.cardType = CardType.PSYCHIC
        self.retreat = [CardType.COLORLESS]; self.weakness = [CardType.DARK]; self.resistance = [CardType.FIGHTING]
        self.evolveFrom = []; self.prize = 1
        self.energy = []; self.attachment = []; self.evolved = []
        self.attacks = [
            Attack({"name": "渡魂","damage": 0,"cost": [CardType.PSYCHIC],"text": "选择自己弃牌区中最多3张「夜巡灵」，放于备战区。"})
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
            if action.attack.name == "渡魂":
                # 从弃牌区选最多3只夜巡灵放到备战区
                duskulls = [c for c in player.discard if c.superType == SuperType.POKEMON and hasattr(c,'name') and '夜巡灵' in str(c.name)]
                if duskulls:
                    max_put = min(3, len(duskulls), 5 - len(player.bench))
                    tips = _t("attack.duskull.spirit_crossing")
                    acts = choose_card_actions(player.id, player.id, 0, max_put, duskulls, tips=tips, source=self)
                    chosen = yield from reduce_choose_card_actions(acts, state)
                    if chosen:
                        for c in chosen:
                            if c in player.discard:
                                move_cards(c, (player.id, CardPosition.DISCARD), (player.id, CardPosition.BENCH), state)
                auto_end_turn(state)
            else:
                yield from reduce_attack_action(action, state)
