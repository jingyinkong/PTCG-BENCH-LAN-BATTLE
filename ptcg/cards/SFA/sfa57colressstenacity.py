"""Colress's Tenacity - SFA 57"""
from ptcg.core.action import UseSupporterAction, choose_card_actions
from ptcg.core.card import SupporterCard
from ptcg.core.enums import CardPosition, CardType, EnergyType, SuperType
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import current_player, move_cards, shuffle_cards
from ptcg.i18n import t as _t


class SFA57ColressTenacity(SupporterCard):
    """Colress's Tenacity - Supporter. Search deck for 1 Energy and 1 Pokémon."""
    def __init__(self):
        super().__init__()
        self.set_name = "SFA"
        self.number = "057"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "阿克罗马的执着"
        self.cardType = CardType.NONE
        self.text = "选择自己牌库中的1张能量卡与1张宝可梦卡（「拥有规则的宝可梦」除外），在给对手看过之后，加入手牌。并重洗牌库。"

    def get_actions(self, state):
        actions = []
        player = current_player(state)
        if not player.supporterPlayedTurn:
            actions.append(UseSupporterAction(state.turn, self))
        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseSupporterAction):
            player = current_player(state)
            move_cards(self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state)
            # 选1张能量
            energies = [c for c in player.left if c.superType == SuperType.ENERGY]
            if energies:
                tips = _t("supporter.colress_tenacity.energy")
                actions = choose_card_actions(player.id, player.id, 0, 1, energies, tips=tips, source=self)
                chosen = yield from reduce_choose_card_actions(actions, state)
                if chosen and chosen[0] in player.left:
                    move_cards(chosen[0], (player.id, CardPosition.LEFT), (player.id, CardPosition.HAND), state)
            # 选1张宝可梦(非规则宝可梦)
            pokemons = [c for c in player.left if c.superType == SuperType.POKEMON 
                       and not (hasattr(c, 'pokemonRule') and c.pokemonRule and c.pokemonRule.value != 'NONE')]
            if pokemons:
                tips = _t("supporter.colress_tenacity.pokemon")
                actions = choose_card_actions(player.id, player.id, 0, 1, pokemons, tips=tips, source=self)
                chosen = yield from reduce_choose_card_actions(actions, state)
                if chosen and chosen[0] in player.left:
                    move_cards(chosen[0], (player.id, CardPosition.LEFT), (player.id, CardPosition.HAND), state)
            shuffle_cards(player.left)
            player.supporterPlayedTurn = True
