from fastapi import FastAPI

from imago.api.routes import router as api_router
from imago.config.settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.include_router(api_router)
    return app


app = create_app()


def run() -> None:
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "imago.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.env == "development",
    )
