from fastapi import APIRouter

from app.api.v1 import admin_scenarios, auth, scenarios, sessions, ws

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(scenarios.router)
api_router.include_router(sessions.router)
api_router.include_router(admin_scenarios.router)

# ws.router is intentionally NOT included here.
# The WebSocket route (/ws/conversation) must be registered directly on the app
# (without the /api prefix) so the frontend can connect at ws://host/ws/conversation.
ws_router = ws.router
