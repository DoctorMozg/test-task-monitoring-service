import datetime
from datetime import timedelta

import pytest
import pytest_asyncio
from asyncpg import Pool
from pydantic_core import Url

from mservice.database.monitor_dao import MonitorDao, WrongRegexException
from mservice.utils import utc_tz_now


@pytest_asyncio.fixture
async def generate_items(monitor_dao: MonitorDao):
    generated_ids = []

    async def generate_items_impl(amount: int):
        new_items = []
        for i in range(amount):
            ind = min(max(i * 5, 5), 300)
            item_id = await monitor_dao.create(
                Url(f"http://test{i}.url"), timedelta(seconds=ind), r".*"
            )
            new_items.append(item_id)

        generated_ids.extend(new_items)

        return new_items

    yield generate_items_impl

    for item in generated_ids:
        await monitor_dao.remove(item)


@pytest.mark.asyncio
async def test_creation(monitor_dao: MonitorDao):
    created_id = await monitor_dao.create(
        Url("http://test.url"), timedelta(seconds=30), r".*"
    )
    assert created_id >= 0, "Has not created item with ID"

    value = await monitor_dao.count()
    assert value == 1, f"1 item should be created, not {value}"


@pytest.mark.asyncio
async def test_creation_malformed_regexp(monitor_dao: MonitorDao):
    with pytest.raises(WrongRegexException):
        await monitor_dao.create(
            Url("http://test.url"), timedelta(seconds=30), r".+@^[A"
        )


@pytest.mark.asyncio
async def test_list(monitor_dao: MonitorDao, generate_items):
    await generate_items(50)

    items = await monitor_dao.select_unlocked(60)
    assert len(items) == 50, "Not all items are selected"


@pytest.mark.asyncio
async def test_reschedule(monitor_dao: MonitorDao, generate_items):
    new_item_ids = await generate_items(50)

    current_time = utc_tz_now()
    rescheduled_items = await monitor_dao.reschedule(new_item_ids)

    assert len(rescheduled_items) == len(new_item_ids), "Not all items are rescheduled"

    for r_item in rescheduled_items:
        assert r_item.next_sync > current_time, "Schedule must be in the future"


@pytest.mark.asyncio
async def test_list_mt(database: Pool, generate_items):
    await generate_items(50)

    conn1 = await database.acquire()
    conn2 = await database.acquire()

    async with conn1.transaction(), conn2.transaction():
        mdao1 = MonitorDao(conn1)
        mdao2 = MonitorDao(conn2)

        items1 = await mdao1.select_unlocked(30)
        assert len(items1) == 30, "Not all items are selected"

        items2 = await mdao2.select_unlocked(30)
        assert len(items2) == 20, "Should get only 20 which are left unlocked"

    items3 = await mdao1.select_unlocked(60)
    assert len(items3) == 50, "Must have all items unlocked after the transactions"


@pytest.mark.asyncio
async def test_removal(monitor_dao: MonitorDao):
    pre_test_count = await monitor_dao.count()

    created_id = await monitor_dao.create(
        Url("http://test.url"), timedelta(seconds=90), r".*"
    )

    assert await monitor_dao.count() == pre_test_count + 1, "1 item should be added"

    result = await monitor_dao.remove(created_id)
    assert result, "Item is not found and not removed"
    assert await monitor_dao.count() == pre_test_count, \
        "Must get back to the original count"

    result = await monitor_dao.remove(created_id)
    assert not result, "Item should not be found"
