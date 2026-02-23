import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse

from app.config import get_settings
from app.database import engine
from app.middleware import RequestLoggingMiddleware
from app.routers import health


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    settings = get_settings()
    logger = logging.getLogger(__name__)
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)
    yield
    await engine.dispose()
    logger.info("Shutting down %s", settings.APP_NAME)


def create_app() -> FastAPI:
    """Application factory that creates and configures the FastAPI instance."""
    settings = get_settings()

    # Configure logging
    logging.basicConfig(
        level=settings.LOG_LEVEL.upper(),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
        docs_url=None,  # Disable default Swagger
        redoc_url=None,  # Disable default ReDoc
    )

    @app.get("/docs", include_in_schema=False)
    async def rapidoc_html() -> HTMLResponse:
        """Serve RapiDoc Custom UI."""
        html = f"""
        <!doctype html> <!-- Important: must specify -->
        <html>
        <head>
            <meta charset="utf-8"> <!-- Important: ios -->
            <script type="module" src="https://unpkg.com/rapidoc/dist/rapidoc-min.js"></script>
            <title>{settings.APP_NAME} - API Docs</title>
        </head>
        <body>
            <rapi-doc 
                spec-url="/openapi.json"
                theme="dark"
                render-style="read"
                show-header="false"
                allow-server-selection="false"
                allow-authentication="true"
            > </rapi-doc>
        </body>
        </html>
        """
        return HTMLResponse(html)

    # Middleware (order matters — last added is executed first)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(health.router)

    return app
