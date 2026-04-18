# Chuc Nang Luyen Noi Realtime

Tai lieu nay giai thich lai chuc nang luyen noi hien tai cua AI Talk Practice sau khi backend da duoc refactor sang mo hinh hoi thoai hybrid kieu ELSA.

## 1. Muc tieu chuc nang

Chuc nang luyen noi giup nguoi hoc thuc hanh tieng Anh theo mot tinh huong cu the, vi du:

- goi do uong tai quan ca phe
- phong van xin viec
- hoi dong nghiep giup do
- hoi dap voi cham soc khach hang
- du lich
- tro chuyen hang ngay

He thong khong chi gui transcript len LLM roi lay cau tra loi. Backend hien tai co them lop dieu phoi hoi thoai de:

- giu dung chu de cua scenario
- nho cac thong tin ngan han ma nguoi hoc vua noi
- xu ly cau tra loi lac de, qua ngan, vo nghia hoac xin goi y
- tao prompt gon cho LLM thay vi gui toan bo lich su chat
- van giu cam giac hoi thoai tu nhien, khong thanh chatbot kich ban cung nhac

## 2. Tong quan trai nghiem nguoi dung

Luong trai nghiem chinh:

1. Nguoi dung chon mot scenario.
2. Frontend mo WebSocket den backend.
3. Backend tao practice session.
4. AI mo dau bang cau hoi phu hop voi scenario.
5. Nguoi dung bam mic va noi.
6. Backend nhan audio realtime, chuyen thanh transcript bang ASR.
7. Khi co final transcript, backend phan tich cau noi cua nguoi dung.
8. He thong quyet dinh:
   - tiep tuc hoi thoai bang LLM
   - hoi lai don gian hon
   - dua hint
   - redirect ve scenario
   - ghi nho thong tin ca nhan huu ich
9. AI tra loi bang text streaming va audio TTS streaming.
10. Session luu lai message va memory de resume neu can.

## 3. Cac thanh phan chinh

### Frontend

Frontend chu yeu nam o:

- `frontend/src/features/practice/pages/PracticeSessionPage.jsx`
- `frontend/src/features/practice/services/realtimeAudio.js`
- `frontend/src/features/practice/api/practiceApi.js`

Frontend gui `metadata.conversation_engine = "lesson_v1"` khi bat dau session. Backend hien tai map `lesson_v1` sang hybrid conversation orchestrator, nen frontend chua can doi schema ngay.

### WebSocket router

Backend WebSocket nam o:

- `backend/app/modules/sessions/routers/ws.py`

Router nay phu trach:

- accept WebSocket
- xac thuc token
- tao hoac resume session
- khoi tao ASR, LLM, TTS qua provider factory
- nhan audio chunk tu frontend
- gui transcript, text chunk, audio chunk ve frontend
- persist user/assistant message
- emit cac event tuong thich voi frontend nhu `lesson_started`, `lesson_state`, `objective_progress`

Router khong nen chua business logic hoi thoai phuc tap. Logic do duoc dua sang orchestrator.

### ConversationSession

File:

- `backend/app/modules/sessions/services/conversation.py`

`ConversationSession` quan ly pipeline realtime:

```text
audio -> ASR -> final transcript -> reply text -> TTS -> audio
```

No phu trach:

- mo va dong ASR session
- feed audio chunk vao ASR provider
- emit `transcript_partial` va `transcript_final`
- goi callback tao reply
- stream `llm_chunk` va `llm_done`
- stream `audio_chunk` va `audio_done`
- xu ly interrupt assistant
- luu user/assistant message qua callback

Trong normal mode, `ConversationSession` co the goi LLM truc tiep. Trong `lesson_v1`, no dung callback streaming tu `DialogueOrchestrator`.

### Hybrid conversation orchestrator

Package moi:

- `backend/app/services/conversation/`

Thanh phan quan trong:

- `scenario.py`: tao `ScenarioDefinition` tu model `Scenario`
- `memory.py`: quan ly short-term session memory
- `fact_extractor.py`: trich xuat fact tu cau noi cua nguoi hoc
- `analyzer.py`: phan tich topic relevance va intent
- `state_controller.py`: dieu khien phase theo soft state machine
- `response_policy.py`: quyet dinh repair, hint, redirect hoac generate
- `prompt_builder.py`: tao prompt gon cho LLM
- `orchestrator.py`: dieu phoi toan bo mot luot hoi thoai
- `evaluation.py`: hook mo rong cho cham diem sau nay

## 4. Luong xu ly mot luot noi

Khi nguoi dung noi xong mot cau:

1. ASR tra ve final transcript.
2. Backend gui `transcript_final` ve frontend.
3. Backend luu user message vao database.
4. `DialogueOrchestrator.stream_turn(user_text)` duoc goi.
5. Orchestrator trich xuat fact, vi du:
   - `profession = designer`
   - `likes = coffee`
   - `concern = nervous about interview`
   - `need = help writing this document`
6. Orchestrator phan tich cau tra loi:
   - `ON_TOPIC`
   - `PARTIALLY_ON_TOPIC`
   - `OFF_TOPIC`
   - `NONSENSE`
   - `HELP_REQUEST`
   - `TOO_SHORT`
   - `CLARIFICATION_REQUEST`
7. State controller quyet dinh giu phase, tien phase, hoac tang repair count.
8. Response policy quyet dinh cach tra loi:
   - generate bang LLM
   - hoi lai
   - dua hint
   - redirect ve scenario
   - acknowledge ngan roi steer back
9. Neu can LLM, prompt builder tao prompt compact.
10. Text duoc stream ra frontend va dua vao TTS.
11. Backend luu assistant message.
12. Memory va dialogue state duoc persist vao session metadata.

## 5. Session memory

Memory ngan han duoc luu trong:

```text
session.session_metadata["hybrid_conversation"]
```

Ben trong co:

- `memory`
- `dialogue_state`
- `scenario_definition`

Memory khong luu full raw chat history khong gioi han. No chi giu:

- cac fact huu ich
- phase hien tai
- objective hien tai
- recent turns da cat gon
- rolling summary ngan
- repair reason gan nhat

Vi du:

```json
{
  "facts": [
    {
      "key": "profession",
      "value": "designer",
      "category": "profile",
      "confidence": 0.82
    },
    {
      "key": "likes",
      "value": "coffee",
      "category": "preference",
      "confidence": 0.78
    }
  ],
  "current_phase_id": "clarify_need",
  "recent_dialogue_summary": "User said they need help writing a document."
}
```

## 6. Prompt LLM moi

Trong orchestrated mode, backend khong gui toan bo `_messages` len LLM nua.

Prompt moi chi gom:

- scenario title
- AI role
- learner role
- objective
- current phase
- topic boundaries
- selected learner facts
- compact recent summary
- current user turn
- instruction giu dung topic
- instruction tra loi ngan, tu nhien, dung cho speech
- instruction chi hoi mot cau hoi moi turn

Muc tieu la giam context dai, giam drift va giu response on-topic hon.

## 7. Xu ly cau tra loi lac de hoac khong tot

He thong co repair behavior rieng:

- `NONSENSE`: hoi lai ro hon
- `TOO_SHORT`: yeu cau them mot chi tiet cu the
- `HELP_REQUEST`: dua cau mau ngan roi moi nguoi hoc thu lai
- `OFF_TOPIC`: keo ve scenario hien tai
- `PARTIALLY_ON_TOPIC`: ghi nho fact huu ich neu co, nhung van giu muc tieu chinh

Vi du trong scenario goi ca phe:

- User: `Cappuccino.`
- Analyzer phai coi day la cau tra loi hop le trong ordering scenario, khong duoc redirect.

Vi du off-topic:

- User: `My cat likes dancing on the moon.`
- AI: `Let's stay with the roleplay. What can I get for you today?`

## 8. WebSocket event protocol

### Client -> Server

- `session_start`
- `config`
- `start_recording`
- `audio_chunk`
- `stop_recording`
- `interrupt_assistant`

### Server -> Client

- `session_started`
- `lesson_started`
- `lesson_state`
- `objective_progress`
- `recording_started`
- `transcript_partial`
- `transcript_final`
- `llm_chunk`
- `llm_done`
- `audio_chunk`
- `audio_done`
- `asr_no_input`
- `assistant_interrupted`
- `conversation_end`
- `session_finalized`
- `error`

Frontend van nhan `lesson_state` theo shape cu de tranh can migration schema ngay.

## 9. Provider factory van duoc giu nguyen

He thong van giu abstraction provider:

- ASR provider
- LLM provider
- TTS provider

Factory nam o:

- `backend/app/infra/factory.py`

Contract nam o:

- `backend/app/infra/contracts.py`

Hybrid orchestrator nam ben tren provider layer. No khong thay the provider factory, chi dieu phoi khi nao va prompt nao duoc gui den LLM.

## 10. Cac loi can de y

### Topic relevance qua chat

Neu analyzer qua chat, user noi mot cau ngan hop le nhu `Latte please` co the bi coi la `TOO_SHORT` hoac `OFF_TOPIC`. Vi vay analyzer co rule rieng cho domain ordering/menu/cafe.

### TTS websocket close

Log dang chu y:

```text
websocket closed due to Invalid close frame
```

Neu xay ra trong DashScope TTS, day la van de o provider realtime TTS hoac cach close websocket cua DashScope SDK. No khac voi logic orchestrator. Neu response text da dung nhung khong co audio, can debug provider TTS rieng.

### Resume session

Khi frontend reconnect voi `session_id`, backend load lai:

```text
session_metadata["hybrid_conversation"]
```

Neu metadata nay mat hoac sai schema, session van co the khoi tao lai state moi, nhung se mat memory ngan han.

## 11. Tom tat ngan

Chuc nang luyen noi hien tai la:

```text
Realtime speaking practice + scenario controller + compact memory + LLM response + TTS audio
```

Backend khong con phu thuoc hoan toan vao LLM cho moi quyet dinh hoi thoai. LLM duoc dung de tao cau tra loi tu nhien khi can, con viec giu topic, nho fact, xu ly cau lac de va dieu khien phase do orchestrator rule-based dam nhan.
