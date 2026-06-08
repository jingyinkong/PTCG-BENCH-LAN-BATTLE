"""Giratina VSTAR - LOR 131"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import auto_end_turn, check_energy, current_player, opponent_active, opponent_player


class LOR131GiratinaVSTAR(PokemonCard):
    """Giratina VSTAR - Pokemon. HP: 280.
    Attack: Star Requiem - KO opponent's Active if 10+ cards in Lost Zone."""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "LOR"; self.number = "131"; self.id = f"{self.set_name}-{self.number}"
        self.name = "骑拉帝纳VSTAR"; self.hp = 280
        self.pokemonType = PokemonType.VSTAR; self.pokemonRule = PokemonRule.NONE; self.stage = Stage.VSTAR
        self.cardType = CardType.DRAGON
        self.retreat = [CardType.COLORLESS]*2; self.weakness = []; self.resistance = []
        self.evolveFrom = ["骑拉帝纳V"]; self.prize = 2
        self.energy = []; self.attachment = []; self.evolved = []
        self.attacks = [
            Attack({"name": "放逐冲击","damage": 160,"cost": [CardType.GRASS,CardType.PSYCHIC,CardType.COLORLESS],"text": "选择附着于自己场上宝可梦身上的2个能量，放于放逐区。"}),
            Attack({"name": "星耀安魂曲","damage": 0,"cost": [CardType.GRASS,CardType.PSYCHIC],"text": "只有放逐区有10张以上卡牌时才可使用。使对手战斗宝可梦昏厥。"})
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
            if action.attack.name == "放逐冲击":
                # 选择2个能量从场上放逐(简化:从自身弃2个能量)
                discard_count = min(2, len(self.energy))
                for _ in range(discard_count):
                    if self.energy: self.energy.pop(0)
                yield from reduce_attack_action(action, state)
            elif action.attack.name == "星耀安魂曲":
                opponent = opponent_player(state)
                lost_zone_count = len(player.discard)  # 简化: 用弃牌区近似放逐区
                if lost_zone_count >= 10 and opponent.active:
                    # KO对手战斗宝可梦
                    opponent.active[0].hp = 0
                auto_end_turn(state)
            else:
                yield from reduce_attack_action(action, state)
