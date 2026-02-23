from app.routers import health_router
from app.config import get_settings


@health_router.get("")
async def health_check() -> dict:
    """Health check endpoint for load balancers and monitoring."""
    settings = get_settings()
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }
