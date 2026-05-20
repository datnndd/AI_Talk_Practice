# BuddyTalk - AI Talk Practice

BuddyTalk là phần mềm luyện giao tiếp tiếng Anh với AI theo thời gian thực. Người dùng có thể chọn chủ đề, nói chuyện bằng micro, nhận phản hồi từ AI, luyện phát âm, học bài theo lộ trình và theo dõi tiến độ qua điểm thưởng, hồ sơ cá nhân, bảng xếp hạng.

Link tham khảo/demo: [buddytalk.mrddat247.id.vn](https://buddytalk.mrddat247.id.vn)

## Hình ảnh phần mềm

> Thêm ảnh chụp màn hình vào thư mục `docs/screenshots/`, rồi cập nhật đường dẫn bên dưới.

| Màn hình | Ảnh |
| --- | --- |
| Trang giới thiệu | ![Landing page](docs/screenshots/landing.png) |
| Đăng nhập / đăng ký | ![Auth page](docs/screenshots/auth.png) |
| Luyện nói với AI | ![Practice session](docs/screenshots/practice.png) |
| Bài học / lộ trình | ![Learning page](docs/screenshots/learning.png) |
| Hồ sơ / bảng xếp hạng | ![Profile and leaderboard](docs/screenshots/profile-leaderboard.png) |
| Trang quản trị | ![Admin page](docs/screenshots/admin.png) |

## Chức năng chính

- Luyện hội thoại tiếng Anh với AI qua micro và WebSocket realtime.
- Chuyển giọng nói thành văn bản bằng ASR, tạo phản hồi bằng LLM, đọc phản hồi bằng TTS.
- Quản lý kịch bản luyện nói, nhân vật AI, bài học và nội dung học tập.
- Đánh giá phát âm, gợi ý câu trả lời, chấm kết quả phiên luyện tập.
- Tài khoản người dùng, đăng nhập, refresh token, hồ sơ cá nhân.
- Gamification: điểm, streak, huy hiệu, cửa hàng, bảng xếp hạng.
- Trang admin quản lý người dùng, thanh toán, nhân vật, kịch bản, bài học, cấu hình website.

## Công nghệ sử dụng

- Frontend: React, Vite, React Router, CSS, Playwright.
- Backend: FastAPI, SQLAlchemy async, Alembic, PostgreSQL.
- AI services: OpenAI-compatible LLM, Deepgram ASR, DashScope TTS, Azure Speech assessment.
- Auth/Payment/Storage tuỳ chọn: JWT, Google OAuth, Stripe, Supabase.

## Cấu trúc thư mục

```text
AI_Talk_Practice/
├── backend/                 # FastAPI API, realtime websocket, database, AI services
├── frontend/                # React + Vite client
├── static/                  # Static assets
├── logs/                    # Log files khi chạy local
└── README.md
```

## Yêu cầu môi trường

- Python 3.11+.
- Node.js 20+.
- PostgreSQL 15+.
- API key cần thiết nếu dùng đủ tính năng AI:
  - `OPENAI_API_KEY`
  - `DEEPGRAM_API_KEY`
  - `DASHSCOPE_API_KEY`
  - `AZURE_SPEECH_KEY` và `AZURE_SPEECH_REGION` nếu dùng đánh giá phát âm.

## Setup backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Tạo file `backend/.env`:

```env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/ai_talk_practice
FRONTEND_URL=http://localhost:5173
JWT_SECRET_KEY=change-this-secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
JWT_REFRESH_EXPIRE_MINUTES=10080

ASR_PROVIDER=deepgram
LLM_PROVIDER=openai
TTS_PROVIDER=dashscope

OPENAI_API_KEY=your_openai_key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-5.1

DEEPGRAM_API_KEY=your_deepgram_key
DEEPGRAM_ASR_MODEL=nova-3

DASHSCOPE_API_KEY=your_dashscope_key
TTS_MODEL=qwen3-tts-flash
TTS_VOICE=Cherry

AZURE_SPEECH_KEY=your_azure_speech_key
AZURE_SPEECH_REGION=eastasia
AZURE_SPEECH_LANGUAGE=en-US

GOOGLE_CLIENT_ID=
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
```

Chạy migration và seed dữ liệu mẫu:

```powershell
alembic upgrade head
python -m app.seed
python -m app.seed_curriculum_lessons
```

Chạy backend:

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Kiểm tra API:

```powershell
curl http://localhost:8000/
curl http://localhost:8000/api/health
```

## Setup frontend

```powershell
cd frontend
npm install
```

Tạo file `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000/api
```

Chạy frontend:

```powershell
npm run dev
```

Mở trình duyệt:

```text
http://localhost:5173
```

## Tạo tài khoản admin

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python scripts/create_admin.py
```

Sau đó đăng nhập bằng tài khoản admin để vào các màn hình quản trị.

## Chạy bằng Docker

Backend và frontend đã có `Dockerfile` riêng:

```powershell
docker build -t buddytalk-backend ./backend
docker build -t buddytalk-frontend ./frontend
```

Khi chạy Docker, cần truyền biến môi trường tương tự file `backend/.env` và `frontend/.env`, đồng thời đảm bảo container backend truy cập được PostgreSQL.

## Kiểm thử

Backend:

```powershell
cd backend
pytest
```

Frontend:

```powershell
cd frontend
npm run lint
npm run test:e2e
```

## Link tham khảo

- Website demo: [https://buddytalk.mrddat247.id.vn](https://buddytalk.mrddat247.id.vn)
- FastAPI: [https://fastapi.tiangolo.com](https://fastapi.tiangolo.com)
- React: [https://react.dev](https://react.dev)
- Vite: [https://vite.dev](https://vite.dev)
- SQLAlchemy: [https://www.sqlalchemy.org](https://www.sqlalchemy.org)
- Alembic: [https://alembic.sqlalchemy.org](https://alembic.sqlalchemy.org)
- Deepgram: [https://deepgram.com](https://deepgram.com)
- OpenAI API: [https://platform.openai.com/docs](https://platform.openai.com/docs)
- Alibaba Cloud DashScope: [https://www.alibabacloud.com/help/en/model-studio](https://www.alibabacloud.com/help/en/model-studio)
- Azure AI Speech: [https://learn.microsoft.com/azure/ai-services/speech-service](https://learn.microsoft.com/azure/ai-services/speech-service)

## Ghi chú bảo mật

- Không commit file `.env` thật hoặc API key thật lên Git.
- Đổi `JWT_SECRET_KEY` trước khi deploy.
- Chỉ bật CORS cho domain frontend thật khi deploy production.
- Dùng HTTPS cho micro, đăng nhập, thanh toán và realtime audio.
