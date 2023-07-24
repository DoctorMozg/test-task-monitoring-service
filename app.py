import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Depends

from mservice.api import init_routers
from mservice.database.migration import create_all_tables
from mservice.dependencies import db_pool
from mservice.utils import prepare_logger

logger = logging.getLogger(__name__)


def init_middleware(main_app: FastAPI):
    @main_app.middleware('http')
    async def log_request(request: Request, call_next):
        start = time.monotonic()
        try:
            logger.info('Request has started')
            return await call_next(request)
        finally:
            logger.info(f'Request has ended. Elapsed time: {time.monotonic() - start}')


def create_application():
    prepare_logger()

    main_app = FastAPI(
        title="URL monitoring service",
    )

    init_middleware(main_app)
    init_routers(main_app)

    return main_app


app = create_application()
