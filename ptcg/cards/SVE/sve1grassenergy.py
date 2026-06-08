"""Grass Energy - SVE 001"""
from ptcg.core.action import AttachEnergyAction
from ptcg.core.card import EnergyCard
from ptcg.core.enums import CardType, EnergyType
from ptcg.core.reducer import reduce_attach_energy_action
from ptcg.utils.utils import can_attach_energy, current_all_pokemon


class SVE001GrassEnergy(EnergyCard):
    """Basic Energy card."""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "SVE"
        self.number = "001"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "基本草能量"
        self.cardType = CardType.GRASS
        self.energyType = EnergyType.BASIC
        self.provides = [CardType.GRASS]

    def get_actions(self, state):
        if not can_attach_energy(state):
            return []
        return [AttachEnergyAction(state.turn, self, p) for p in current_all_pokemon(state)]

    def reduce_action(self, action, state):
        if isinstance(action, AttachEnergyAction):
            reduce_attach_energy_action(action, state)
