from dataclasses import dataclass
from typing import Annotated

from asyncpg import Pool
from fastapi import Depends

from mservice.database.base import create_pool


class DatabasePoolHolder:

    def __init__(self):
        self._pool = None

    async def provide_pool(self):
        """
        Lazily initializes and returns pool of connections
        :return: initialized pool
        """
        if self._pool is None:
            self._pool = await create_pool()

        return self._pool


pool_holder = DatabasePoolHolder()


async def db_pool():
    """
    Global connection pool dependency.
    :return: initialized connection pool
    """
    return await pool_holder.provide_pool()


async def db_connection(pool: Annotated[Pool, Depends(db_pool)]):
    """
    Returns one connection from pool
    :param pool: injected pool
    :return: working DB connection
    """
    async with pool.acquire() as conn:
        yield conn
