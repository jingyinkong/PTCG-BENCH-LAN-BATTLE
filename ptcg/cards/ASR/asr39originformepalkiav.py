"""Origin Forme Palkia V - ASR 039"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction, choose_card_actions
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import CardPosition, CardType, PokemonPosition, PokemonRule, PokemonType, Stage, SuperType
from ptcg.core.reducer import reduce_attack_action, reduce_choose_card_actions, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import auto_end_turn, check_energy, current_player, move_cards, opponent_active, shuffle_cards
from ptcg.i18n import t as _t


class ASR039OriginFormePalkiaV(PokemonCard):
    """Origin Forme Palkia V - BASIC Pokemon. HP: 220."""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "ASR"; self.number = "039"; self.id = f"{self.set_name}-{self.number}"
        self.name = "起源帕路奇亚V"; self.hp = 220
        self.pokemonType = PokemonType.V; self.pokemonRule = PokemonRule.NONE; self.stage = Stage.BASIC
        self.cardType = CardType.WATER
        self.retreat = [CardType.COLORLESS]*2; self.weakness = [CardType.LIGHTNING]; self.resistance = []
        self.evolveFrom = []; self.prize = 2
        self.energy = []; self.attachment = []; self.evolved = []
        self.attacks = [
            Attack({"name": "领域支配","damage": 0,"cost": [CardType.COLORLESS],"text": "选择牌库中1张竞技场，给对手看过加入手牌。重洗牌库。"}),
            Attack({"name": "水炮破坏","damage": 120,"cost": [CardType.WATER,CardType.WATER,CardType.COLORLESS],"text": "下一个自己的回合，这只宝可梦无法使用招式。"})
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
            if action.attack.name == "领域支配":
                # 从牌库搜1张竞技场
                stadiums = [c for c in player.left if c.superType == SuperType.TRAINER and 'StadiumCard' in str(type(c).__mro__)]
                if stadiums:
                    tips = _t("ability.origin_palkia_v.stadium_dominance")
                    acts = choose_card_actions(player.id, player.id, 0, 1, stadiums, tips=tips, source=self)
                    chosen = yield from reduce_choose_card_actions(acts, state)
                    if chosen and chosen[0] in player.left:
                        move_cards(chosen[0], (player.id, CardPosition.LEFT), (player.id, CardPosition.HAND), state)
                shuffle_cards(player.left)
                auto_end_turn(state)
            elif action.attack.name == "水炮破坏":
                yield from reduce_attack_action(action, state)
                self._cannot_attack_next_turn = True
                auto_end_turn(state)
            else:
                yield from reduce_attack_action(action, state)
