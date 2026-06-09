from ptcg.core.ability import PassiveAbility
"""Kyurem - SFA 047"""
from ptcg.core.action import AttackAction, EffectAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction, choose_card_actions
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.effect import Effect
from ptcg.core.enums import AbilityTrigger, AbilityType, CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_choose_card_actions, reduce_effect_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import auto_end_turn, check_energy, current_player, opponent_active, opponent_bench, opponent_player


class SFA047Kyurem(PokemonCard):
    """Kyurem - BASIC Pokemon. HP: 130.
    Attack: Trifrost - Discard all Energy, deal 110 to 3 opponent Pokemon."""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "SFA"; self.number = "047"; self.id = f"{self.set_name}-{self.number}"
        self.name = "酋雷姆"; self.hp = 130
        self.pokemonType = PokemonType.NORMAL; self.pokemonRule = PokemonRule.NONE; self.stage = Stage.BASIC
        self.cardType = CardType.WATER
        self.retreat = [CardType.COLORLESS]*2; self.weakness = [CardType.METAL]; self.resistance = []
        self.evolveFrom = []; self.prize = 1
        self.energy = []; self.attachment = []; self.evolved = []
        self.ability = [
            PassiveAbility({
                "name": "反等离子",
                "abilityType": AbilityType.PASSIVE_ABILITY,
                "abilityTrigger": AbilityTrigger.ATTACKING,
                "onceUsedPerTurn": False,
                "text": "这只宝可梦使用招式的伤害，因对手战斗宝可梦身上附加的等离子能量而增加20。"
            })
        ]
        self.attacks = [
            Attack({"name": "三重冰霜","damage": 0,"cost": [CardType.WATER,CardType.WATER,CardType.COLORLESS],"text": "将这只宝可梦身上附着的所有能量放于弃牌区，给对手的3只宝可梦，各造成110伤害。"})
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
            if action.attack.name == "三重冰霜":
                player = current_player(state)
                opponent = opponent_player(state)
                # 弃掉所有能量
                self.energy.clear()
                # 对对手最多3只宝可梦造成110伤害
                all_opp = opponent.active + list(opponent.bench)
                effect = Effect(11)  # 11 damage counters = 110 HP
                for target in all_opp[:3]:
                    yield from reduce_effect_action(EffectAction(player.id, self, effect, target), state)
                auto_end_turn(state)
            else:
                yield from reduce_attack_action(action, state)
