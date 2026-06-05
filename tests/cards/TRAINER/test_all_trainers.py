"""Level 3: 全量训练家卡属性验证。"""
import pytest
from ptcg.core.card_registry import registry
from ptcg.core.card import ItemCard, SupporterCard, StadiumCard, ToolCard, TrainerCard
from ptcg.core.enums import SuperType, TrainerType

registry._ensure_loaded()
ALL_TRAINER_IDS = [cid for cid in registry.list_all()
                   if isinstance(registry.get(cid)(), TrainerCard)]


@pytest.mark.unit
@pytest.mark.parametrize("cid", ALL_TRAINER_IDS)
def test_trainer_card_has_correct_supertype(cid):
    card = registry.get(cid)()
    assert card.superType == SuperType.TRAINER, f"{cid}: expected TRAINER, got {card.superType}"
    assert hasattr(card, 'trainerType'), f"{cid}: missing trainerType"


@pytest.mark.unit
@pytest.mark.parametrize("cid", ALL_TRAINER_IDS)
def test_trainer_card_has_text(cid):
    card = registry.get(cid)()
    assert hasattr(card, 'text'), f"{cid}: missing text attribute"
    # Most trainer cards should have effect text
    if not isinstance(card, ToolCard) and not isinstance(card, StadiumCard):
        assert card.text, f"{cid}: empty text"


@pytest.mark.unit
@pytest.mark.parametrize("cid", ALL_TRAINER_IDS)
def test_trainer_card_has_valid_name(cid):
    card = registry.get(cid)()
    assert card.name, f"{cid}: empty name"
    assert len(card.name) > 0
