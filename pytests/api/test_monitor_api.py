import datetime

import pytest
from httpx import AsyncClient
from pydantic_core import Url

from mservice.database.monitor_dao import MonitorDao
from mservice.utils import utc_tz_now


@pytest.mark.asyncio
async def test_creation(client: AsyncClient, monitor_dao: MonitorDao):
    rv = await client.post(
        '/monitors/',
        json={
            "url": "https://test.com",
            "frequency_sec": 100,
            "regexp": None
        }
    )
    rv.raise_for_status()

    result: dict = rv.json()
    assert result['id'] > 0, 'Should have an ID assigned'

    present_items = await monitor_dao.select_unlocked(
        utc_tz_now(), 1000
    )
    assert len(present_items) == 1, 'Item should be in the database and returned'


@pytest.mark.asyncio
async def test_deletion(client: AsyncClient, monitor_dao: MonitorDao):
    id = await monitor_dao.create(
        Url("http://someurl.com"), datetime.timedelta(seconds=1), None
    )

    rv = await client.delete(f'/monitors/{id}/')
    rv.raise_for_status()

    result: dict = rv.json()
    assert result['removed'], 'Should be true if removed an entity'

    present_items = await monitor_dao.select_unlocked(
        utc_tz_now(), 1000
    )
    assert len(present_items) == 0, 'All items should be removed and not found'
