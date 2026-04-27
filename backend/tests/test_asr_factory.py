import pytest

from app.core.config import Settings
from app.infra.asr.deepgram_asr import DeepgramASR
from app.infra.factory import create_asr


def test_create_asr_uses_deepgram_by_default():
    asr = create_asr(Settings(_env_file=None))
    assert isinstance(asr, DeepgramASR)


def test_create_asr_rejects_removed_dashscope_provider():
    with pytest.raises(ValueError, match="Available: deepgram"):
        create_asr(Settings(asr_provider="dashscope"))
