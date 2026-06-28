from fastapi import FastAPI

from iotables.platform.router import router as platform_router


def create_app() -> FastAPI:
    app = FastAPI(title="IoTables API")
    app.include_router(platform_router)
    return app


app = create_app()
