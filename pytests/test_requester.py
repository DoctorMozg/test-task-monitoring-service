from unittest.mock import AsyncMock

import pytest
from pydantic_core import Url

from mservice.requester import request_url, RequestSuccessSchema, RequestFailedSchema


@pytest.mark.asyncio
async def test_requester(mock_httpx_get):
    async_mock: AsyncMock = mock_httpx_get(status_code=200, json={"some": "True"})
    result_returned = await request_url(Url('https://existing.io/'))
    async_mock.assert_awaited_once()
    assert isinstance(result_returned, RequestSuccessSchema)
    assert result_returned.http_status == 200
    assert len(result_returned.body) > 0, "Response must have a body"
    assert result_returned.response_time


@pytest.mark.asyncio
async def test_requester_failed(mock_httpx_get_failed):
    result_returned = await request_url(Url('https://somerandomtext.text/'))
    mock_httpx_get_failed.assert_awaited_once()
    assert isinstance(result_returned, RequestFailedSchema)
    assert len(result_returned.error) > 0, "Result must have an error"
