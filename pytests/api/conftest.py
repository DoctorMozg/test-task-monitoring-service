from typing import AsyncGenerator

import pytest_asyncio
from httpx import AsyncClient

from app import create_application


@pytest_asyncio.fixture
async def client(event_loop) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
            app=create_application(), base_url="http://testserver"
    ) as cl:
        yield cl
