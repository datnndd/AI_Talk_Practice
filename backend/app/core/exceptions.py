import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from app.core.config import settings

logger = logging.getLogger(__name__)

def setup_exception_handlers(app: FastAPI):
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        
        detail = "Internal server error"
        if settings.is_debug:
            detail = str(exc)
            
        return JSONResponse(
            status_code=500,
            content={"detail": detail},
        )
