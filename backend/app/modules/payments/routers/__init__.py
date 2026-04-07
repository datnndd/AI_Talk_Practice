from .payments import router
from .admin import router as admin_router

__all__ = ["router", "admin_router"]
