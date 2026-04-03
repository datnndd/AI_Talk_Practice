import pytest
from app.services.variation_service import VariationService
from app.schemas.session import SessionCreate
from app.core.config import settings

@pytest.mark.asyncio
async def test_build_variation_seed_determinism():
    seed1 = VariationService.build_variation_seed(
        scenario_id=1,
        parameters={"p": 1},
        mode="roleplay"
    )
    seed2 = VariationService.build_variation_seed(
        scenario_id=1,
        parameters={"p": 1},
        mode="roleplay"
    )
    assert seed1 == seed2
    
    # Different order index of parameters should still produce same seed
    seed3 = VariationService.build_variation_seed(
        scenario_id=1,
        parameters={"b": 2, "a": 1},
        mode="roleplay"
    )
    seed4 = VariationService.build_variation_seed(
        scenario_id=1,
        parameters={"a": 1, "b": 2},
        mode="roleplay"
    )
    assert seed3 == seed4

@pytest.mark.asyncio
async def test_resolve_variation_pregenerated(db_session, test_scenario, test_variation):
    # test_variation is pregenerated and approved in the fixture
    payload = SessionCreate(
        scenario_id=test_scenario.id,
        prefer_pregenerated=True
    )
    variation = await VariationService.resolve_variation_for_session(
        db_session,
        scenario=test_scenario,
        payload=payload
    )
    assert variation is not None
    assert variation.id == test_variation.id
    assert variation.is_pregenerated is True
    assert variation.usage_count == 1 # 0 from fixture + 1 from resolve

@pytest.mark.asyncio
async def test_resolve_variation_realtime_creation(db_session, test_scenario):
    payload = SessionCreate(
        scenario_id=test_scenario.id,
        variation_parameters={"level": "advanced"},
        create_variation_if_missing=True,
        mode="roleplay"
    )
    variation = await VariationService.resolve_variation_for_session(
        db_session,
        scenario=test_scenario,
        payload=payload
    )
    assert variation is not None
    assert variation.scenario_id == test_scenario.id
    assert variation.parameters == {"level": "advanced"}
    assert variation.is_pregenerated is False
    assert "Conversation mode: roleplay" in variation.system_prompt_override

@pytest.mark.asyncio
async def test_resolve_variation_not_found(db_session, test_scenario):
    payload = SessionCreate(
        scenario_id=test_scenario.id,
        variation_id=9999
    )
    from app.core.exceptions import NotFoundError
    with pytest.raises(NotFoundError):
        await VariationService.resolve_variation_for_session(
            db_session,
            scenario=test_scenario,
            payload=payload
        )
