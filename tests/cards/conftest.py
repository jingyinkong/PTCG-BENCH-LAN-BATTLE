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
        card_class = card_registry.get(card_id)
        if card_class is None:
            raise ValueError(f"Card not found: {card_id}")
        return card_class()
    return _get_card
