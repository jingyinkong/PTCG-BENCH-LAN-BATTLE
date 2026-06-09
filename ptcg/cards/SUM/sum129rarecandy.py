"""神奇糖果 - 道具卡。将手牌中1张2阶进化宝可梦直接叠放在场上对应的基础宝可梦上完成进化。"""
from ptcg.core.action import EvolvePokemonAction, UseItemAction, choose_card_actions
from ptcg.core.card import ItemCard, PokemonCard
from ptcg.core.enums import CardPosition, CardType, Stage
from ptcg.core.reducer import reduce_choose_card_actions
from ptcg.utils.utils import current_all_pokemon, current_player, get_basic_pokemon_name, move_cards
from ptcg.i18n import t as _t


class SUM129RareCandy(ItemCard):
    """神奇糖果 - SUM 129"""
    def __init__(self):
        super().__init__()
        self.set_name = "SUM"
        self.number = "129"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "神奇糖果"
        self.cardType = CardType.NONE
        self.text = "选择自己场上的1只基础宝可梦，若手牌中有该宝可梦进化而来的2阶进化宝可梦，则将其叠放在该宝可梦身上完成进化。首回合或当回合放置的宝可梦不可使用。"

    def get_actions(self, state):
        player = current_player(state)
        actions = []
        found = False
        # 检查手牌中是否有可以进化的2阶宝可梦
        for card in player.hand:
            if not (isinstance(card, PokemonCard) and card.stage == Stage.STAGE_2):
                continue
            for pokemon in current_all_pokemon(state):
                if pokemon.name == get_basic_pokemon_name(card) and not pokemon.firstTurnPlayed:
                    found = True
                    break
        if found:
            actions.append(UseItemAction(player.id, self))
        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseItemAction):
            player = current_player(state)
            # 将自身弃入弃牌堆
            move_cards(self, (player.id, CardPosition.HAND),
                       (player.id, CardPosition.DISCARD), state)
            # 筛选手牌中可进化的2阶宝可梦
            evolved_cardlist = []
            for card in player.hand:
                if not (isinstance(card, PokemonCard) and card.stage == Stage.STAGE_2):
                    continue
                for pokemon in current_all_pokemon(state):
                    if pokemon.name == get_basic_pokemon_name(card):
                        evolved_cardlist.append(card)
                        break
            # 选择要进化成的2阶宝可梦
            tips = _t("item.rare_candy.choose_stage2")
            actions = choose_card_actions(player.id, player.id, 1, 1, evolved_cardlist, tips=tips, source=self)
            evolved_card = yield from reduce_choose_card_actions(actions, state)
            evolved_card = evolved_card[0]
            # 选择场上的目标基础宝可梦
            evolving_cardlist = []
            for pokemon in current_all_pokemon(state):
                if pokemon.name == get_basic_pokemon_name(evolved_card):
                    evolving_cardlist.append(pokemon)
            tips = _t("item.rare_candy.choose_basic")
            actions = choose_card_actions(player.id, player.id, 1, 1, evolving_cardlist, tips=tips, source=self)
            evolving_card = yield from reduce_choose_card_actions(actions, state)
            evolving_card = evolving_card[0]
            # 执行进化
            yield from evolved_card.reduce_action(
                EvolvePokemonAction(player.id, evolved_card, evolving_card), state)
