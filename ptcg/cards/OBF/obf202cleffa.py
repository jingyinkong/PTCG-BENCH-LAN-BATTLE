"""Cleffa - OBF 202"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import CardPosition, CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import auto_end_turn, check_energy, current_player, move_cards, opponent_active


class OBF202Cleffa(PokemonCard):
    """Cleffa - BASIC Pokemon. HP: 30.
    Attack: Grabby Draw - Draw until hand has 7 cards."""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "OBF"; self.number = "202"; self.id = f"{self.set_name}-{self.number}"
        self.name = "皮宝宝"; self.hp = 30
        self.pokemonType = PokemonType.NORMAL; self.pokemonRule = PokemonRule.NONE; self.stage = Stage.BASIC
        self.cardType = CardType.PSYCHIC
        self.retreat = []; self.weakness = [CardType.METAL]; self.resistance = []
        self.evolveFrom = []; self.prize = 1
        self.energy = []; self.attachment = []; self.evolved = []
        self.attacks = [
            Attack({"name": "握握抽取","damage": 0,"cost": [],"text": "从牌库上方抽取卡牌，直到自己的手牌变为7张为止。"})
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
            if action.attack.name == "握握抽取":
                # 抽牌直到手牌7张
                while len(player.hand) < 7 and player.left:
                    move_cards(player.left[0], (player.id, CardPosition.LEFT), (player.id, CardPosition.HAND), state)
                auto_end_turn(state)
            else:
                yield from reduce_attack_action(action, state)
