from fastapi import APIRouter

from app.api.v1 import auth, scenarios, sessions, ws

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(scenarios.router)
api_router.include_router(sessions.router)
api_router.include_router(ws.router)
