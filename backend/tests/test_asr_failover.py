import pytest

from app.core.config import Settings
from app.infra.contracts import TranscriptEvent, TranscriptType
from app.infra.factory import create_asr


class PrimaryFailingASR:
    def __init__(self):
        self.started = False
        self.closed = False
        self.feed_count = 0

    async def start_session(self, language="en", sample_rate=16000):
        self.started = True

    async def feed_audio(self, audio_chunk: bytes):
        self.feed_count += 1
        if self.feed_count >= 2:
            raise RuntimeError("primary feed failure")

    async def get_transcript(self):
        return None

    async def stop_session(self):
        return None

    async def close(self):
        self.closed = True


class SecondaryRecordingASR:
    def __init__(self):
        self.started = False
        self.audio_chunks: list[bytes] = []

    async def start_session(self, language="en", sample_rate=16000):
        self.started = True

    async def feed_audio(self, audio_chunk: bytes):
        self.audio_chunks.append(audio_chunk)

    async def get_transcript(self):
        return None

    async def stop_session(self):
        return TranscriptEvent(
            text=f"replayed:{len(self.audio_chunks)}",
            type=TranscriptType.FINAL,
            language="en",
        )

    async def close(self):
        return None


@pytest.mark.asyncio
async def test_failover_asr_replays_buffered_audio():
    from app.infra.asr.failover_asr import FailoverASR

    primary = PrimaryFailingASR()
    secondary = SecondaryRecordingASR()
    asr = FailoverASR(
        primary=primary,
        secondary=secondary,
        primary_name="deepgram",
        secondary_name="dashscope",
    )

    await asr.start_session(language="en", sample_rate=16000)
    await asr.feed_audio(b"first")
    await asr.feed_audio(b"second")
    result = await asr.stop_session()

    assert primary.started is True
    assert primary.closed is True
    assert secondary.started is True
    assert secondary.audio_chunks == [b"first", b"second"]
    assert result == TranscriptEvent(text="replayed:2", type=TranscriptType.FINAL, language="en")


def test_create_asr_uses_deepgram_failover_by_default():
    from app.infra.asr.failover_asr import FailoverASR

    asr = create_asr(Settings())
    assert isinstance(asr, FailoverASR)
