"""薄雾能量 - TEF 161"""
from ptcg.core.action import AttachEnergyAction
from ptcg.core.card import EnergyCard
from ptcg.core.enums import CardPosition, CardType, EnergyType
from ptcg.core.reducer import reduce_attach_energy_action
from ptcg.utils.utils import can_attach_energy, current_all_pokemon


class TEF161MistEnergy(EnergyCard):
    """特殊能量卡。"""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "TEF"
        self.number = "161"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "薄雾能量"
        self.cardType = CardType.COLORLESS
        self.energyType = EnergyType.SPECIAL
        self.provides = [CardType.COLORLESS]
        self.text = "只要这张卡牌，被附着于宝可梦身上，就被视作1个【无】能量。  身上附着了这张卡牌的宝可梦，不受到对手宝可梦所使用的招式的效果影响。（已经受到的效果，不会消失。）"

    def get_actions(self, state):
        if not can_attach_energy(state):
            return []
        return [AttachEnergyAction(state.turn, self, p) for p in current_all_pokemon(state)]

    def reduce_action(self, action, state):
        if isinstance(action, AttachEnergyAction):
            reduce_attach_energy_action(action, state)
