import datetime
import logging
from dataclasses import dataclass

import httpx
from pydantic import AnyUrl, validate_call, NonNegativeInt

from mservice import settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RequestSuccessSchema:
    response_time: datetime.timedelta
    http_status: NonNegativeInt
    body: str


@dataclass(frozen=True, slots=True)
class RequestFailedSchema:
    error: str


@validate_call
async def request_url(url: AnyUrl) -> RequestSuccessSchema | RequestFailedSchema:
    """
    Makes a request to the provided URL and returns all needed metadata.
    :param url: URL to look at
    :return: RequestSuccessSchema if everything is fine or RequestFailedSchema
    when encountered an error
    """
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                str(url),
                timeout=settings.REQUEST_TIMEOUT
            )

            return RequestSuccessSchema(
                response_time=r.elapsed,
                http_status=r.status_code,
                body=r.text,
            )
    except Exception as e:
        logger.exception(f"Failed getting {url} page")
        return RequestFailedSchema(error=str(e))
