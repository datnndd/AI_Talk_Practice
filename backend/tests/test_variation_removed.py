from app.db.base_class import Base
from app.modules.sessions.models.session import Session


def test_scenario_variation_model_is_not_registered():
    assert "scenario_variations" not in Base.metadata.tables
    assert not hasattr(Session, "variation_id")
    assert not hasattr(Session, "variation")
