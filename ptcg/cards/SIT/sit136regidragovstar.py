"""Regidrago VSTAR - SIT 136"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import auto_end_turn, check_energy, current_player, opponent_active


class SIT136RegidragoVSTAR(PokemonCard):
    """Regidrago VSTAR - Pokemon. HP: 280.
    Attack: Dragon Impunity - Use any attack from a Dragon Pokemon in your discard pile."""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "SIT"; self.number = "136"; self.id = f"{self.set_name}-{self.number}"
        self.name = "雷吉铎拉戈VSTAR"; self.hp = 280
        self.pokemonType = PokemonType.VSTAR; self.pokemonRule = PokemonRule.NONE; self.stage = Stage.VSTAR
        self.cardType = CardType.DRAGON
        self.retreat = [CardType.COLORLESS]*3; self.weakness = []; self.resistance = []
        self.evolveFrom = ["雷吉铎拉戈V"]; self.prize = 2
        self.energy = []; self.attachment = []; self.evolved = []
        self.attacks = [
            Attack({"name": "巨龙无双","damage": 0,"cost": [CardType.GRASS,CardType.FIRE],"text": "选择自己弃牌区中的【龙】宝可梦所拥有的1个招式，作为这个招式使用。"})
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
            if action.attack.name == "巨龙无双":
                player = current_player(state)
                # 从弃牌区找龙宝可梦，复制其攻击
                dragon_pokemon = [c for c in player.discard if hasattr(c,'cardType') and c.cardType == CardType.DRAGON and hasattr(c,'attacks') and c.attacks]
                if dragon_pokemon:
                    # 使用第一只龙宝可梦的第一个攻击
                    copied_attack = dragon_pokemon[0].attacks[0]
                    action.attack.damage = copied_attack.damage
                yield from reduce_attack_action(action, state)
                auto_end_turn(state)
            else:
                yield from reduce_attack_action(action, state)
