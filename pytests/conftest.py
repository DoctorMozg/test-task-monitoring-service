import asyncio
from asyncio import AbstractEventLoop
from datetime import timedelta
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from asyncpg import Connection, Pool
from httpx import Response
from pytest_mock import MockerFixture

from mservice.database.base import create_pool
from mservice.database.migration import create_all_tables
from mservice.database.monitor_dao import MonitorDao


@pytest.yield_fixture(scope='session')
def event_loop(request):
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def database_pool(event_loop: AbstractEventLoop):
    async def drop_tables(conn):
        await conn.execute('DROP TABLE IF EXISTS monitor_log;')
        await conn.execute('DROP TABLE IF EXISTS monitors;')

    async def base_db_init() -> Pool:
        db_pool = await create_pool()
        async with db_pool.acquire() as connection:
            await drop_tables(connection)
            await create_all_tables(connection)

        return db_pool

    async def base_db_cleanup(db_pool: Pool):
        async with db_pool.acquire() as connection:
            await drop_tables(connection)

    pool = event_loop.run_until_complete(base_db_init())

    yield pool

    event_loop.run_until_complete(base_db_cleanup(pool))


@pytest_asyncio.fixture()
async def database(database_pool: Pool):
    async def clear_db(conn):
        await conn.execute('DELETE FROM monitor_log;')
        await conn.execute('DELETE FROM monitors;')

    async with database_pool.acquire() as connection:
        await clear_db(connection)

    return database_pool


@pytest_asyncio.fixture()
async def db_connection(database: Pool):
    async with database.acquire() as connection:
        yield connection


@pytest.fixture
def monitor_dao(db_connection: Connection):
    return MonitorDao(db_connection)


@pytest.fixture
def mock_httpx_get(mocker: MockerFixture):
    async_mock = AsyncMock()
    mocker.patch(
        'httpx.AsyncClient.get',
        side_effect=async_mock
    )

    def set_mock_params(status_code: int, json: dict):
        response = Response(status_code=status_code, json=json)
        response._elapsed = timedelta(seconds=1)
        async_mock.return_value = response

        return async_mock

    yield set_mock_params


@pytest.fixture
def mock_httpx_get_failed(mocker: MockerFixture):
    async_mock = AsyncMock()
    mocker.patch(
        'httpx.AsyncClient.get',
        side_effect=async_mock
    )

    async_mock.side_effect = Exception("Mocked exception")

    yield async_mock
