import datetime
from unittest.mock import AsyncMock

import pytest
from pydantic_core import Url

from mservice.database.models import MonitorModel
from mservice.scheduler import _sync_item
from mservice.utils import utc_tz_now


@pytest.fixture
def monitor_model_generator():
    def generate_mm(url: str, regexp: str | None):
        return MonitorModel(
            id=0,
            url=Url(url),
            regexp=regexp,
            active=True,
            sync_interval=datetime.timedelta(seconds=1),
            next_sync=utc_tz_now()
        )

    return generate_mm


@pytest.mark.parametrize(
    'regexp, has_regexp',
    [
        pytest.param(
            None,
            False,
            id='no regexp',
        ),
        pytest.param(
            r".*some.*",
            True,
            id='found regexp',
        ),
        pytest.param(
            r".*other.*",
            False,
            id='not found regexp',
        ),
    ]
)
@pytest.mark.asyncio
async def test_normal_sync(
        mock_httpx_get,
        monitor_model_generator,
        regexp: str | None,
        has_regexp
):
    mon_model: MonitorModel = monitor_model_generator("http://someurl.com", regexp)
    async_mock: AsyncMock = mock_httpx_get(status_code=200, json={"some": "True"})

    model_id, result = await _sync_item(mon_model)
    async_mock.assert_awaited_once()
    assert model_id == mon_model.id
    assert result.http_status == 200
    assert result.regexp_found == has_regexp
    assert result.error is None


@pytest.mark.asyncio
async def test_failed_sync(mock_httpx_get_failed: AsyncMock, monitor_model_generator):
    mon_model: MonitorModel = monitor_model_generator("http://someurl.com", None)
    model_id, result = await _sync_item(mon_model)
    mock_httpx_get_failed.assert_awaited_once()
    assert model_id == mon_model.id
    assert result.http_status == 0
    assert result.error is not None
