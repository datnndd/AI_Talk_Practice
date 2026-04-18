# Luồng Hoạt Động Chi Tiết của Chức Năng Hội Thoại Với AI

Chức năng hội thoại với AI được xây dựng xoay quanh cơ chế giao tiếp Realtime hai chiều bằng **WebSocket**, kết hợp mô hình xử lý chuỗi luồng xử lý: **ASR (Speech-to-Text) -> Dialogue Orchestrator (LLM) -> TTS (Text-to-Speech)** nhằm đảm bảo độ trễ thấp nhất.

Dưới đây là sơ đồ và chi tiết luồng hoạt động từ góc nhìn Hệ thống (frontend và backend).

## 1. Khởi tạo phiên kết nối (Initialization)
1. **Frontend**: Người dùng mở trang `PracticeSessionPage`. Trình duyệt khởi tạo kết nối WebSocket (`new WebSocket`) tới endpoint `/ws/conversation` trên backend. Trình duyệt xin cấp quyền truy cập Microphone và gán các `AudioContext` cùng `AudioWorklet` để chuẩn bị bắt audio.
2. **Frontend -> Backend**: Gửi gói tin JSON `session_start` đính kèm theo `token` xác thực của người dùng, `scenario_id` (kịch bản bài học) và tuỳ chọn `conversation_engine: lesson_v1`.
3. **Backend**:
   - Hàm `websocket_conversation` (trong `ws.py`) xác thực phiên. Nó lấy bản ghi người học, scenario và session details từ Database.
   - Backend khởi tạo đối tượng `ConversationSession` (nằm trong `conversation.py`).
   - Khởi tạo 3 service AI cơ bản: **ASR** (nhận diện giọng), **LLM** (mô hình ngôn ngữ) và **TTS** (tổng hợp giọng nói).
   - Nếu kịch bản yêu cầu (`lesson_v1`), nó xây dựng thêm `DialogueOrchestrator` (nằm trong `hybrid_conversation/`).
4. **Backend -> Frontend**: Trả về `session_started` báo hiệu sẵn sàng bắt đầu.
5. **Backend chủ động mở lời**: Nếu kịch bản có thiết lập câu hỏi khai mạc (opening chunk), hệ thống gọi trực tiếp `speak_opening`. Backend sinh ra text mở bài kèm audio (thông qua TTS) để AI chủ động lên tiếng trước mà không cần đợi User. 

---

## 2. Quá trình Thu âm và Nhận dạng Giọng nói (ASR - Audio Recording)
1. **Frontend**: Người dùng nhấn/giữ nút bắt đầu nói, trình duyệt gửi sự kiện `start_recording` để đánh thức Backend. Lập tức thu âm thanh thông qua microphone theo định dạng **PCM 16kHz 1 kênh**.
2. **Frontend -> Backend (`audio_chunk`)**: AudioWorklet liên tục lấy các mẫu chunk audio của user từ Microphone, buffer lại và được mã hoá base64, sau đó bơm liên tục qua dòng WebSocket bằng packet `audio_chunk`.
3. **Backend (`feed_audio`)**: Lớp `ConversationSession` nhận base64 chunks này, giải mã bytes và nạp âm thanh này (`feed_audio`) vào Audio Stream của ASR Engine tĩnh đang chạy (ví dụ như Google/Whisper).
4. **Polling ASR**: Song song lúc này, hệ thống sẽ liên tục polling (thăm dò) ASR engine cho event phân giải:
   - Khi có text nháp (`TranscriptType.PARTIAL`), backend gửi sự kiện `transcript_partial` ngay về cho frontend -> **Frontend** gõ text realtime vào khung nhập để người dùng thấy text xuất hiện khi họ vừa nhả chữ.

---

## 3. Khóa Lượt Thoại User & Xác định đoạn Script Text (Finalize Turn)
1. **Frontend**: Người dùng nhả phím dừng thu âm (gửi `stop_recording`), hoặc ASR engine tự động nhận diện đã hết câu (trả về Event `SPEECH_END`).
2. **Backend**: 
   - Đóng tiến trình nạp (feed) audio vào ASR, chốt lại chuỗi string hoàn thiện nhất để lấy `transcript_final` làm tin nhắn gửi từ User.
   - Thông điệp thoại được lưu trực tiếp vào database (`SessionService.add_message`).
3. **Backend -> Frontend (`transcript_final`)**: Chuỗi kết quả chốt cuối này được gửi về Frontend. UI chuyển text partial thành nội dung user tin nhắn hoàn chỉnh màu xanh bên phải khung `ChatWindow`.

---

## 4. Trải qua LLM và Tạo Phản Hồi Từ AI (Response Pipeline)
1. **Backend LLM Stream**: Message vừa xong của user được chuyển đến `DialogueOrchestrator.stream_turn(user_text)`.
   - LLM sẽ dựa vào scenario, bộ nguyên tắc AI, và session/progress hiện tại để sinh ra câu trả lời theo dạng Stream.
   - Trong quá trình sinh từ, AI không chờ dòng text hoàn tất, thay vào đó liên tục pump các Token đã đẻ ra qua packet `llm_chunk` ngược về Frontend.
2. **Frontend (Text Generation)**: Các token mới tới tới sẽ liên tục ghép tạo hiệu ứng Typewriter cho khung phản hồi của AI.
3. **Backend (TTS Stream - Audio Synthesis)**:
   - Để tối ưu độ trễ, mỗi token text từ LLM sinh ra cũng lập tức đi thẳng vào TTS Generator (Text-to-Speech) thông qua `_tts.synthesize_stream`.
   - Engine TTS kết xuất ra các gói nhị phân âm thanh (PCM). Backend bắn các gói phân mảnh này thẳng về frontend dưới kiện JSON `audio_chunk` base64.
4. **Frontend (Audio Playback)**: Hàm `queuePlaybackChunk` gọi Buffer API trong Web Audio (`AudioContext`), chuyển base64 sang Float32Array PCM để phát. Vì luồng là Async Buffer, nó sẽ xếp nối đuôi nhau và tạo trải nghiệm nói chuyện không bị giật lác hay ngắt quãng.

---

## 5. Kết Luận Lượt Đợi & Cập Nhật Logic Khóa Học
- Khi LLM chạy xong và phun xong token, gửi `llm_done` báo hiệu ngắt dòng chat.
- Khi TTS chạy xong byte audio luồng cuối, gửi cờ `audio_done` tới frontend cho phép cất icon Sound Wave đi.
- **Backend -> Frontend**: Trong suốt tiến trình gọi hội thoại, nếu có thay đổi trong `lesson_state` (User đạt được mục tiêu nhỏ trong scenario), backend sẽ gửi sự kiện `lesson_state` mới kèm theo `objective_progress`. Ui sidebar hiển thị đánh tick bài học lập tức được sáng lên.

---

## 6. Luồng Đặc Biệt: Ngắt Lời (Interrupt) & Cạn Thời Gian
- **Interrupt (Cướp quyền nói)**: Chức năng cho phép User không cần chờ AI nói xong mà bấm Record lại ngay lúc nào tuỳ thích.
  - Khi thu âm giữa chừng, backend nhận được `interrupt_assistant`, nó lập tức **hủy luồng asyncio task response**, ngừng buffer audio, báo LLM dừng text loop, gạch đi phần text AI chưa nói kịp vào database và chuẩn bị nhận lệnh thu âm mới.
- **Cạn thời lượng**: Nếu backend task `run_timeout_after` quét đếm ngược (dựa vào tham số `estimated_duration` cấu hình sẵn) bằng 0. Nó sẽ Force cancel mọi request stream hiện tại. Gọi sự kiện WS `conversation_end` kèm nguyên nhân `time_limit_reached`. Trình duyệt lập tức báo đỏ, close socket, và gọi hàm `navigateToResult` đẩy người chơi vào UI chấm điểm. Đồng thời, backend đặt lệnh `run_final_evaluation()` vào background job để AI tiến hành phân tích log chat và chấm bài.
