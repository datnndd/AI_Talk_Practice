# AI Talk Practice - Realtime Conversation Backend

Real-time AI conversation backend: **Microphone → ASR → LLM → TTS → Speaker**

## Architecture

```
Browser (Mic) ──WebSocket──▶ FastAPI Backend
                              ├── ASR: Deepgram Nova-3
                              ├── LLM: OpenAI Responses API
                              └── TTS: DashScope
```

## Quick Start

### 1. Get API Keys

| Provider | Key | Get it at |
|----------|-----|-----------|
| **OpenAI Responses API** | `OPENAI_API_KEY` | Your OpenAI API key |
| **Deepgram** (ASR) | `DEEPGRAM_API_KEY` | [Deepgram Console](https://console.deepgram.com/) |
| **DashScope** (TTS) | `DASHSCOPE_API_KEY` | [Alibaba Cloud Model Studio](https://modelstudio.console.alibabacloud.com/) |

### 2. Setup & Run

```bash
cd backend

# First run — creates .env from template:
bash run.sh

# Edit .env with your API keys:
nano .env

# Run again:
bash run.sh

### 3. Test

```bash
# Health check
curl http://localhost:8000/

# Check providers
curl http://localhost:8000/providers
```

## Configuration (.env)

```env
# Switch providers by changing these:
ASR_PROVIDER=deepgram           # deepgram
LLM_PROVIDER=openai             # OpenAI Responses API
TTS_PROVIDER=dashscope          # dashscope

# API Keys
DEEPGRAM_API_KEY=dg-xxx
DASHSCOPE_API_KEY=sk-xxx
OPENAI_API_KEY=sk-xxx

# Models
LLM_MODEL=gpt-5.1
LLM_BASE_URL=https://api.openai.com/v1
DEEPGRAM_ASR_MODEL=nova-3
TTS_MODEL=qwen3-tts-flash
TTS_VOICE=Cherry
```

## WebSocket Protocol

**Endpoint:** `ws://localhost:8000/ws/conversation`

### Client → Server

| Type | Data | Description |
|------|------|-------------|
| `start_recording` | `{language: "en"}` | Begin ASR session |
| `audio_chunk` | `{data: "<base64 PCM>"}` | Send audio (16kHz, 16-bit, mono) |
| `stop_recording` | — | End ASR, trigger LLM + TTS |
| `config` | `{language, voice}` | Update settings |

### Server → Client

| Type | Data | Description |
|------|------|-------------|
| `ready` | — | Session initialized |
| `transcript_final` | `{text}` | Final ASR result |
| `llm_chunk` | `{text}` | LLM response chunk |
| `llm_done` | `{text}` | Complete LLM response |
| `audio_chunk` | `{data: "<base64 PCM>"}` | TTS audio (24kHz) |
| `audio_done` | — | All audio sent |
| `error` | `{message}` | Error occurred |

## Adding a New Provider

1. Create file in `app/services/{asr,llm,tts}/`
2. Implement the base class from `app/services/base.py`
3. Register in `app/services/factory.py`
4. Add config to `.env.example`

Example:
```python
# app/services/asr/my_custom_asr.py
from app.infra.contracts import ASRBase, TranscriptEvent

class MyCustomASR(ASRBase):
    async def start_session(self, language, sample_rate):
        ...
    async def feed_audio(self, audio_chunk):
        ...
    async def get_transcript(self):
        ...
    async def stop_session(self):
        ...
```
