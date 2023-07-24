import logging

import asyncpg
from asyncpg import Pool, Connection

from mservice import settings


logger = logging.getLogger(__name__)


async def create_pool() -> Pool:
    logger.info("Creating database connection pool")
    return await asyncpg.create_pool(
        dsn=settings.DB_CONNECTION_STRING
    )


async def create_connection() -> Connection:
    logger.info("Creating a single database connection")
    return await asyncpg.connect(
        dsn=settings.DB_CONNECTION_STRING
    )
