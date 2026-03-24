1. Chức năng hội thoại giọng nói realtime với AI
Mục tiêu

Người dùng bấm mic, nói chuyện với AI như đang gọi thoại. AI nghe, hiểu, trả lời lại bằng giọng nói gần như ngay lập tức.

Tạm thời sẽ làm
Thu âm từ microphone trên web
Gửi audio theo từng đoạn nhỏ lên server
Server dùng Qwen3-ASR để chuyển speech thành text
Text đó đưa vào mô hình hội thoại
Kết quả trả lời đưa qua Qwen3-TTS để phát thành giọng nói
Hiển thị cả text người dùng nói và text AI trả lời trên màn hình
Hướng làm
Frontend
Dùng MediaRecorder hoặc WebRTC để thu audio
Chia audio thành chunk ngắn, gửi liên tục qua WebSocket
Hiển thị trạng thái:
đang nghe
đang xử lý
AI đang trả lời
Backend
Tạo WebSocket server
Nhận audio chunk
Đưa audio vào pipeline ASR realtime
Khi người dùng dừng nói thì gửi toàn bộ câu sang LLM
Nhận text trả lời từ LLM
Đưa text sang Qwen-TTS để tạo audio
Stream audio ngược lại frontend để phát luôn

2.Chức năng AI đóng vai theo kịch bản
Mục tiêu

AI không nói chuyện chung chung, mà luyện theo tình huống cụ thể như:

gọi món
phỏng vấn xin việc
hỏi đường
giao tiếp công sở
giới thiệu bản thân
Tạm thời sẽ làm
Danh sách scenario có sẵn
Mỗi scenario có:
tên
mô tả
mục tiêu học
vai trò của AI
Người dùng chọn scenario trước khi bắt đầu nói chuyện

3.Chức năng sửa lỗi câu nói của người dùng
Mục tiêu

Sau khi người dùng nói hoặc gõ, hệ thống chỉ ra câu chưa tự nhiên hoặc sai ngữ pháp.

Tạm thời sẽ làm
Hiển thị câu người dùng đã nói
Sinh ra câu gợi ý tốt hơn
Giải thích ngắn lỗi chín

4.Chức năng chấm điểm speaking cơ bản
Mục tiêu

Không chỉ nói chuyện, mà còn có đánh giá đơn giản sau mỗi lượt nói.

5.Chức năng phát giọng nói AI
Mục tiêu

AI không chỉ trả text mà còn trả bằng giọng nói tự nhiên.

Tạm thời sẽ làm
1 hoặc 2 giọng cố định
Phát audio tự động sau khi AI trả lời
6.Chức năng lịch sử hội thoại
Mục tiêu

Người dùng có thể xem lại các cuộc hội thoại đã luyện.

Tạm thời sẽ làm
Lưu session hội thoại
Xem danh sách lịch sử
Xem chi tiết từng session
7.Chức năng dashboard tiến bộ cơ bản
Mục tiêu

Cho người dùng thấy mình đã luyện được bao nhiêu và cải thiện ra sao.

Tạm thời sẽ làm
số buổi đã học
tổng thời gian luyện
điểm trung bình
số scenario đã hoàn thành
8.Chức năng quản lý bài học / scenario ở mức admin đơn giản
Mục tiêu

Bạn có thể thêm hoặc sửa các tình huống luyện tập mà không phải sửa code nhiều.
9. Chức năng đăng nhập người dùng
Mục tiêu

Mỗi người dùng có dữ liệu học riêng.

Tạm thời sẽ làm
đăng ký
đăng nhập
lưu profile cơ bản