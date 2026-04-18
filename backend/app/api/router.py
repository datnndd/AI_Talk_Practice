from fastapi import APIRouter

from app.modules.auth.routers import router as auth
from app.modules.payments.routers import admin_router as admin_payments
from app.modules.payments.routers import router as payments
from app.modules.users.routers import admin_router as admin_users
from app.modules.users.routers import router as users
from app.modules.scenarios.routers import user as scenarios
from app.modules.scenarios.routers import admin as admin_scenarios
from app.modules.sessions.routers import lessons
from app.modules.sessions.routers import rest as sessions
from app.modules.sessions.routers import ws
from app.modules.translations.routers import translation

api_router = APIRouter()

api_router.include_router(auth)
api_router.include_router(payments)
api_router.include_router(admin_payments)
api_router.include_router(users)
api_router.include_router(admin_users)
api_router.include_router(scenarios.router)
api_router.include_router(sessions.router)
api_router.include_router(lessons.router)
api_router.include_router(admin_scenarios.router)
api_router.include_router(translation.router, prefix="/translations", tags=["translations"])

# ws.router is intentionally NOT included here.
# The WebSocket route (/ws/conversation) must be registered directly on the app
# (without the /api prefix) so the frontend can connect at ws://host/ws/conversation.
ws_router = ws.router
