from typing import Annotated

from asyncpg import Pool
from fastapi import Depends

from mservice.database.base import create_pool

POOL_HOLDER = {}


async def db_pool():
    """
    Global connection pool. Stores it into the global variable. A little dirty
    but is needed for FastAPI.
    :return: initialized connection pool
    """
    if 'pool' not in POOL_HOLDER:
        POOL_HOLDER['pool'] = await create_pool()
    return POOL_HOLDER['pool']


async def db_connection(pool: Annotated[Pool, Depends(db_pool)]):
    """
    Returns one connection from pool
    :param pool: injected pool
    :return: working DB connection
    """
    async with pool.acquire() as conn:
        yield conn
