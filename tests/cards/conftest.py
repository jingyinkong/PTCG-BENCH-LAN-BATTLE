"""卡牌测试 conftest — 提供卡牌实例化和参考数据 fixture。

pytest 自动发现机制加载此文件。
tests/cards/{SET_CODE}/test_*.py 通过 fixture 名称引用 card_registry、get_card、card_reference。
与 tests/conftest.py 不同：后者为 agent 测试通用 fixture，此为卡牌测试专用。
"""
import json
from pathlib import Path

import pytest

from ptcg.core.card_registry import registry


@pytest.fixture(scope="session")
def card_registry():
    registry._ensure_loaded()
    return registry


@pytest.fixture(scope="session")
def card_reference():
    cache_path = Path(__file__).parent.parent.parent / "card_data_cache.json"
    if cache_path.exists():
        with open(cache_path, encoding="utf-8") as f:
            return json.load(f)
    return {}


@pytest.fixture
def get_card(card_registry):
    def _get_card(card_id: str):
        card_class = card_registry.get(cid)
        if card_class is None:
            raise ValueError(f"Card not found: {card_id}")
        return card_class()
    return _get_card


@pytest.fixture
def snapshot_game():
    """场景快照测试 fixture — 预设游戏状态，用于卡牌效果行为验证。

    返回 SnapshotHelper，支持:
    - set_hand(player, card_ids): 设置玩家手牌
    - set_bench(player, card_ids): 设置后场宝可梦
    - set_active(player, card_id): 设置出战宝可梦
    - set_deck(player, card_ids): 设置牌库
    - assert_hand_count / assert_bench_count / assert_deck_count
    """
    from ptcg.core.deck import Deck
    from ptcg.core.player import Player
    from ptcg.core.state import State
    from ptcg.core.enums import PlayerId, CardPosition

    class SnapshotHelper:
        def __init__(self):
            self.p1 = None
            self.p2 = None
            self.state = None

        def setup(self):
            deck = Deck([])
            self.p1 = Player(deck)
            self.p2 = Player(deck)
            self.p1.id = PlayerId.PLAYER1
            self.p2.id = PlayerId.PLAYER2
            self.state = State(self.p1, self.p2)
            self.state.turn = PlayerId.PLAYER1
            return self

        def _make_cards(self, card_ids):
            cards = []
            for cid in card_ids:
                card_cls = registry.get(cid)
                if card_cls:
                    cards.append(card_cls())
            return cards

        def set_hand(self, player, card_ids):
            cards = self._make_cards(card_ids)
            for c in cards:
                c.cardPosition = CardPosition.HAND
            player.hand = cards

        def set_bench(self, player, card_ids):
            cards = self._make_cards(card_ids)
            for i, c in enumerate(cards):
                c.cardPosition = CardPosition.BENCH
                c.index = i
            player.bench = cards

        def set_active(self, player, card_id):
            cards = self._make_cards([card_id])
            if cards:
                c = cards[0]
                c.cardPosition = CardPosition.ACTIVE
                c.index = 0
                player.active = c

        def set_deck(self, player, card_ids):
            player.left = self._make_cards(card_ids)

        def assert_hand_count(self, player, n):
            assert len(player.hand) == n, f"手牌期望{n}实际{len(player.hand)}"

        def assert_bench_count(self, player, n):
            assert len(player.bench) == n, f"后场期望{n}实际{len(player.bench)}"

        def assert_deck_count(self, player, n):
            assert len(player.left) == n, f"牌库期望{n}实际{len(player.left)}"

    h = SnapshotHelper()
    h.setup()
    return h
