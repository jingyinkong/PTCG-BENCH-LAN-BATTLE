"""Legacy Energy - TWM 167"""
from ptcg.core.action import AttachEnergyAction
from ptcg.core.card import EnergyCard
from ptcg.core.enums import CardType, EnergyType
from ptcg.core.reducer import reduce_attach_energy_action
from ptcg.utils.utils import can_attach_energy, current_all_pokemon


class TWM167LegacyEnergy(EnergyCard):
    """Special Energy card."""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "TWM"
        self.number = "167"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "遗赠能量"
        self.cardType = CardType.COLORLESS
        self.energyType = EnergyType.SPECIAL
        self.provides = [CardType.COLORLESS]
        self.text = "只要这张卡牌，被附着于宝可梦身上，就被视作1个所有属性的能量。   身上附着了这张卡牌的宝可梦，受到对手宝可梦的招式的伤害而【昏厥】时，对手拿取的奖赏卡将减少1张。对战中，自己的「遗赠能量」的这个效果，只会生效1次。"

    def get_actions(self, state):
        if not can_attach_energy(state):
            return []
        return [AttachEnergyAction(state.turn, self, p) for p in current_all_pokemon(state)]

    def reduce_action(self, action, state):
        if isinstance(action, AttachEnergyAction):
            reduce_attach_energy_action(action, state)
