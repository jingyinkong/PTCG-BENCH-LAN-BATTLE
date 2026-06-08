"""Minccino - TEF 136"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction, choose_card_actions
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import CardPosition, CardType, PokemonPosition, PokemonRule, PokemonType, Stage, SuperType
from ptcg.core.reducer import reduce_attack_action, reduce_choose_card_actions, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import auto_end_turn, check_energy, current_player, opponent_active, opponent_player
from ptcg.i18n import t as _t


class TEF136Minccino(PokemonCard):
    """Minccino - BASIC Pokemon. HP: 60.
    Attack: Sweep - Discard up to 2 Pokemon Tools from opponent's field."""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "TEF"; self.number = "136"; self.id = f"{self.set_name}-{self.number}"
        self.name = "泡沫栗鼠"; self.hp = 60
        self.pokemonType = PokemonType.NORMAL; self.pokemonRule = PokemonRule.NONE; self.stage = Stage.BASIC
        self.cardType = CardType.COLORLESS
        self.retreat = [CardType.COLORLESS]; self.weakness = [CardType.FIGHTING]; self.resistance = []
        self.evolveFrom = []; self.prize = 1
        self.energy = []; self.attachment = []; self.evolved = []
        self.attacks = [
            Attack({"name": "扫除","damage": 0,"cost": [CardType.COLORLESS],"text": "选择放于对手场上宝可梦身上最多2张「宝可梦道具」，放于弃牌区。"})
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
            opponent = opponent_player(state)
            if action.attack.name == "扫除":
                # 选对手场上最多2张道具弃掉
                all_opp_pokemon = opponent.active + list(opponent.bench)
                tools = []
                for p in all_opp_pokemon:
                    for att in (p.attachment if hasattr(p,'attachment') else []):
                        if hasattr(att,'superType') and att.superType == SuperType.TRAINER:
                            tools.append((p, att))
                if tools:
                    tool_cards = [t[1] for t in tools]
                    tips = _t("attack.minccino.clean_up")
                    from ptcg.core.reducer import reduce_choose_card_actions as rc
                    acts = choose_card_actions(player.id, player.id, 0, min(2, len(tool_cards)), tool_cards, tips=tips, source=self)
                    chosen = yield from rc(acts, state)
                    if chosen:
                        from ptcg.utils.utils import move_cards
                        for tc in chosen:
                            for p, tool in tools:
                                if tool is tc and tool in p.attachment:
                                    p.attachment.remove(tool)
                                    move_cards(tool, (player.id, CardPosition.BENCH_ATTACHMENT), (opponent.id, CardPosition.DISCARD), state)
                                    break
                auto_end_turn(state)
            else:
                yield from reduce_attack_action(action, state)
