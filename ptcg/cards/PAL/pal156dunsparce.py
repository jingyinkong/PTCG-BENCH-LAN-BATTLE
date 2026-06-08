"""Dunsparce - PAL 156"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction, choose_card_actions
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import CardPosition, CardType, PokemonPosition, PokemonRule, PokemonType, Stage, SuperType
from ptcg.core.reducer import reduce_attack_action, reduce_choose_card_actions, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import auto_end_turn, check_energy, current_player, move_cards, opponent_active, shuffle_cards
from ptcg.i18n import t as _t


class PAL156Dunsparce(PokemonCard):
    """Dunsparce - BASIC Pokemon. HP: 60.
    Attack: Find a Friend - Search deck for 1 Pokemon, reveal and add to hand."""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "PAL"; self.number = "156"; self.id = f"{self.set_name}-{self.number}"
        self.name = "土龙弟弟"; self.hp = 60
        self.pokemonType = PokemonType.NORMAL; self.pokemonRule = PokemonRule.NONE; self.stage = Stage.BASIC
        self.cardType = CardType.COLORLESS
        self.retreat = [CardType.COLORLESS]; self.weakness = [CardType.FIGHTING]; self.resistance = []
        self.evolveFrom = []; self.prize = 1
        self.energy = []; self.attachment = []; self.evolved = []
        self.attacks = [
            Attack({"name": "找朋友","damage": 0,"cost": [CardType.COLORLESS],"text": "选择自己牌库中的1张宝可梦，给对手看过加入手牌。重洗牌库。"})
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
            if action.attack.name == "找朋友":
                pokemon = [c for c in player.left if c.superType == SuperType.POKEMON]
                if pokemon:
                    tips = _t("attack.dunsparce.call_for_family")
                    acts = choose_card_actions(player.id, player.id, 0, 1, pokemon, tips=tips, source=self)
                    chosen = yield from reduce_choose_card_actions(acts, state)
                    if chosen and chosen[0] in player.left:
                        move_cards(chosen[0], (player.id, CardPosition.LEFT), (player.id, CardPosition.HAND), state)
                shuffle_cards(player.left)
                auto_end_turn(state)
            else:
                yield from reduce_attack_action(action, state)
