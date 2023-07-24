from typing import Annotated

from asyncpg import Pool
from fastapi import Depends

from mservice.database.base import create_pool

POOL_HOLDER = {}


async def db_pool():
    if 'pool' not in POOL_HOLDER:
        POOL_HOLDER['pool'] = await create_pool()
    return POOL_HOLDER['pool']


async def db_connection(pool: Annotated[Pool, Depends(db_pool, use_cache=True)]):
    async with pool.acquire() as conn:
        yield conn
