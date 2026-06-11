"""V防守能量 - SIT 169"""
from ptcg.core.action import AttachEnergyAction
from ptcg.core.card import EnergyCard
from ptcg.core.enums import CardPosition, CardType, EnergyType
from ptcg.core.reducer import reduce_attach_energy_action
from ptcg.utils.utils import can_attach_energy, current_all_pokemon


class SIT169VGuardEnergy(EnergyCard):
    """特殊能量卡。"""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "SIT"
        self.number = "169"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "V防守能量"
        self.cardType = CardType.COLORLESS
        self.energyType = EnergyType.SPECIAL
        self.provides = [CardType.COLORLESS]
        self.text = "只要这张卡牌，被附着于宝可梦身上，就被视作1个【无】能量。  身上附有这张卡牌的宝可梦，受到对手「宝可梦V」的招式的伤害「-30」。这个效果，无论身上附有多少张「V防守能量」，都不会叠加。"

    def get_actions(self, state):
        if not can_attach_energy(state):
            return []
        return [AttachEnergyAction(state.turn, self, p) for p in current_all_pokemon(state)]

    def reduce_action(self, action, state):
        if isinstance(action, AttachEnergyAction):
            reduce_attach_energy_action(action, state)
