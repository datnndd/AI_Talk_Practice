# Tài Liệu Chức Năng Nói Chuyện AI Hiện Tại

## 1. Mục tiêu hiện tại

Chức năng "nói chuyện AI" hiện tại của hệ thống không phải là một voice chat tự do hoàn toàn. Ở implementation frontend hiện tại, nó đang chạy theo mô hình:

`guided speaking lesson`

Tức là:

- Người dùng chọn một `scenario`.
- Hệ thống mở một `session` realtime qua WebSocket.
- Người dùng nói qua microphone.
- Backend xử lý theo pipeline `ASR -> phản hồi AI -> TTS`.
- Phản hồi của AI được dẫn dắt bởi `lesson engine` để bám theo mục tiêu học tập của scenario.
- UI hiển thị tiến độ objective, hint, câu hỏi hiện tại và lịch sử hội thoại.

Điểm quan trọng:

- Backend có hỗ trợ mode hội thoại LLM thông thường.
- Nhưng frontend hiện tại luôn gửi `metadata.conversation_engine = "lesson_v1"`.
- Vì vậy trải nghiệm thực tế hiện tại là `AI tutor có kịch bản`, không phải `free-form AI companion`.

## 2. Trải nghiệm người dùng hiện tại

Trong màn `PracticeSessionPage`, người dùng có các hành vi chính:

- Kết nối realtime đến `ws://.../ws/conversation`.
- Bắt đầu một session gắn với `scenario_id`.
- Bấm mic để bắt đầu ghi âm.
- Nói tiếng Anh vào microphone.
- Nhận transcript tạm thời và transcript cuối.
- Nghe phản hồi của AI được stream ra loa.
- Xem câu hỏi hiện tại, objective đang làm, progress %, số follow-up còn lại.
- Xin gợi ý bằng API `POST /lessons/hint`.
- Ngắt lời assistant để nói tiếp.
- Kết thúc buổi luyện tập.

## 3. Luồng kỹ thuật end-to-end

### 3.1 Frontend

Frontend nằm chủ yếu ở:

- `frontend/src/features/practice/pages/PracticeSessionPage.jsx`
- `frontend/src/features/practice/services/realtimeAudio.js`
- `frontend/src/features/practice/api/practiceApi.js`

Luồng xử lý:

1. Frontend tải thông tin scenario qua REST `GET /scenarios/:id`.
2. Frontend mở WebSocket đến `/ws/conversation`.
3. Khi socket mở, frontend gửi:
   - `type: "session_start"`
   - `token`
   - `scenario_id`
   - `language: "en"`
   - `voice: "Cherry"`
   - `metadata: { conversation_engine: "lesson_v1" }`
4. Khi người dùng ghi âm:
   - Trình duyệt lấy mic bằng `getUserMedia`.
   - Audio được resample về `16kHz`.
   - Audio được convert sang `PCM16 mono`.
   - Audio được base64 hóa và gửi dần qua `audio_chunk`.
5. Khi backend trả audio:
   - Frontend nhận `audio_chunk`.
   - Decode base64 về PCM16.
   - Convert sang Float32.
   - Phát audio qua Web Audio API ở `24kHz`.

### 3.2 Backend realtime

Backend realtime nằm chủ yếu ở:

- `backend/app/modules/sessions/routers/ws.py`
- `backend/app/modules/sessions/services/conversation.py`

Khi nhận `session_start`, backend sẽ:

- Xác thực token.
- Tạo `session` trong database.
- Resolve `scenario` và có thể resolve `variation`.
- Lấy `system_prompt` từ variation override hoặc từ `scenario.ai_system_prompt`.
- Nếu `conversation_engine = "lesson_v1"` thì khởi tạo lesson package và state.
- Tạo `ConversationSession`.

### 3.3 Pipeline hội thoại

`ConversationSession` quản lý pipeline:

`audio -> ASR -> user transcript -> AI reply -> TTS -> audio trả về`

Các bước cụ thể:

1. `start_recording`
   - Backend mở ASR session.
   - Poll transcript liên tục.
2. `audio_chunk`
   - Backend feed audio vào ASR provider.
3. Khi ASR có kết quả cuối:
   - Backend phát `transcript_final`.
   - Lưu user message vào database.
4. Nếu đang ở lesson mode:
   - Không dùng LLM để tự nghĩ nội dung trả lời.
   - Gọi `LessonRuntimeService.advance(...)`.
   - Sinh câu trả lời tiếp theo theo objective hiện tại.
5. Text phản hồi được stream ra frontend bằng `llm_chunk`.
6. Cùng lúc text được đưa qua TTS để stream `audio_chunk`.
7. Khi xong:
   - Backend gửi `llm_done`
   - Backend gửi `audio_done`
   - Lưu assistant message vào database.

## 4. Lesson engine hiện tại đang làm gì

Lesson engine nằm ở:

- `backend/app/modules/sessions/services/lesson_runtime.py`

Nó biến `scenario.learning_objectives` thành một lesson có cấu trúc:

- nhiều objective
- mỗi objective có:
  - `goal`
  - `main_question`
  - `follow_up_questions`
  - `expected_points`
  - `hint_seed`

### Cách chấm tiến độ

Mỗi câu trả lời của user được đánh giá theo:

- số từ có ý nghĩa
- mức độ khớp với `expected_points`
- số follow-up đã dùng

Nếu user trả lời đủ:

- objective hiện tại được complete
- hệ thống chuyển sang objective tiếp theo

Nếu chưa đủ:

- AI hỏi follow-up
- hoặc yêu cầu bổ sung point còn thiếu

Khi objective cuối hoàn thành:

- `state.status = "completed"`
- `state.should_end = true`
- backend phát `conversation_end`
- AI đưa ra câu wrap-up thay vì tiếp tục hỏi tiếp

## 5. Hint system hiện tại

Hint hiện tại không đi qua WebSocket, mà đi qua REST:

- `POST /lessons/hint`

Frontend gọi API này khi user bấm xin gợi ý.

Hint trả về gồm:

- `analysis_vi`
- `answer_strategy_vi`
- `keywords`
- `sample_answer`
- `sample_answer_easy`
- `metadata.matched_points`
- `metadata.missing_points`

Hint được cache theo:

- `objective_id`
- nội dung câu trả lời gần nhất của user

## 6. WebSocket protocol hiện tại

### Client -> Server

- `session_start`
  - tạo session realtime
- `config`
  - đổi `language` hoặc `voice`
- `start_recording`
  - bắt đầu 1 lượt nói
- `audio_chunk`
  - gửi audio base64 PCM16
- `stop_recording`
  - kết thúc lượt nói
- `interrupt_assistant`
  - ngắt phần assistant đang nói

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
- `conversation_end`
- `assistant_interrupted`
- `error`

## 7. Dữ liệu được lưu lại

Persistence nằm chủ yếu ở:

- `backend/app/modules/sessions/services/session.py`

Những gì đang được lưu:

- `Session`
  - user
  - scenario
  - variation
  - status
  - mode
  - duration
  - `session_metadata`
- `Message`
  - role: `user` hoặc `assistant`
  - content
  - order_index

Lesson state cũng được lưu trong `session_metadata.lesson`, gồm:

- lesson package
- progress state
- hints cache

Khi WebSocket disconnect:

- nếu đã có ít nhất 1 user turn hoàn chỉnh, session được finalize là `completed`
- nếu chưa có user turn nào, session được đánh dấu `abandoned`

## 8. Hành vi realtime đáng chú ý

### 8.1 Có thể auto-finalize mà không cần bấm stop

Test hiện tại cho thấy nếu ASR phát hiện:

- `FINAL`
- hoặc `SPEECH_END`

thì backend có thể tự finalize lượt nói và chạy phản hồi mà không cần chờ `stop_recording`.

### 8.2 Có hỗ trợ interrupt assistant

Nếu user bấm mic trong lúc assistant đang nói:

- frontend gửi `interrupt_assistant`
- backend dừng response task đang chạy
- có thể persist phần assistant reply đã sinh ra một phần
- frontend có thể auto-start lượt ghi âm mới ngay sau interrupt

### 8.3 LLM history được trim

Trong mode LLM thường, backend chỉ gửi số message gần nhất cho LLM theo cấu hình:

- `llm_history_message_limit`

Điều này giúp tránh phình context.

## 9. Giới hạn hiện tại của chức năng

Đây là các giới hạn thực tế của implementation hiện tại:

- Frontend đang cố định lesson mode, chưa có UI để chuyển sang `free conversation`.
- Chưa thấy text input thực sự gửi message text vào backend; trọng tâm hiện tại là voice turn.
- Hint đang được sinh theo luật và keyword matching, chưa phải một coaching model riêng.
- Completion của session hiện dựa trên số lượt user đã finalize, không phải chất lượng học tập tổng thể.
- Tài liệu cũ trong `backend/README.md` chưa phản ánh đầy đủ protocol mới như `session_started`, `lesson_started`, `conversation_end`, `assistant_interrupted`.

## 10. Tóm tắt ngắn gọn để dùng cho product/team

Chức năng nói chuyện AI hiện tại của bạn là một hệ thống `guided voice practice` theo scenario. Người dùng nói qua mic, backend nhận audio realtime, chuyển giọng nói thành text, đánh giá câu trả lời theo objective của lesson, sinh câu hỏi hoặc follow-up tiếp theo, rồi chuyển phản hồi đó thành audio stream để phát lại ngay trên giao diện. Toàn bộ tiến trình học, transcript cuối và message assistant đều được lưu vào session.

Nếu cần mô tả một câu:

`Đây là AI speaking tutor theo kịch bản có progress tracking, hint và interrupt realtime, chưa phải voice chat tự do hoàn toàn.`
