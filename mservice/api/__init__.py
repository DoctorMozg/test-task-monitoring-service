from fastapi import FastAPI
from mservice.api.monitors import router as monitor_router


def init_routers(app: FastAPI):
    """
    Adds routers to the app
    :param app: FastAPI app
    """
    app.include_router(router=monitor_router)
