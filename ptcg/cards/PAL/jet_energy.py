"""Jet Energy - PAL 190"""
from ptcg.core.action import AttachEnergyAction, PlayPokemonAction
from ptcg.core.card import EnergyCard
from ptcg.core.enums import CardPosition, CardType, EnergyType, SuperType
from ptcg.core.reducer import reduce_attach_energy_action
from ptcg.utils.utils import current_player, move_cards


class PAL190JetEnergy(EnergyCard):
    """Jet Energy - Special Energy. When attached, switch this Pokemon with bench."""
    def __init__(self):
        super().__init__()
        self.set_name = "PAL"; self.number = "190"; self.id = f"{self.set_name}-{self.number}"
        self.name = "喷射能量"
        self.superType = SuperType.ENERGY
        self.energyType = EnergyType.SPECIAL
        self.cardType = CardType.NONE
        self.provides = [CardType.COLORLESS]
        self.text = "这张卡牌附着于宝可梦身上时，提供1个无色能量。将这只宝可梦与备战宝可梦互换。"

    def get_actions(self, state):
        actions = []
        player = current_player(state)
        if self in player.hand:
            if player.active:
                actions.append(AttachEnergyAction(player.id, self, player.active[0]))
            for p in player.bench:
                actions.append(AttachEnergyAction(player.id, self, p))
        return actions

    def reduce_action(self, action, state):
        if isinstance(action, PlayPokemonAction):
            pass
        elif isinstance(action, AttachEnergyAction):
            reduce_attach_energy_action(action, state)
            # 附着后换位
            player = current_player(state)
            if player.active and player.bench:
                old = player.active[0]
                new = player.bench[0]
                move_cards(old, (player.id, CardPosition.ACTIVE), (player.id, CardPosition.BENCH), state)
                move_cards(new, (player.id, CardPosition.BENCH), (player.id, CardPosition.ACTIVE), state)
