import datetime
from typing import Annotated

from pydantic import NonNegativeInt, conint
from pydantic.dataclasses import dataclass

from mservice import settings
from mservice.utils import utc_tz_now

FrequencySec = Annotated[
    int, conint(ge=settings.MIN_PING_INTERVAL, le=settings.MAX_PING_INTERVAL)
]


@dataclass(frozen=True, slots=True)
class SiteMetricSchema:

    @staticmethod
    def from_error(error: str) -> 'SiteMetricSchema':
        return SiteMetricSchema(
            ts=utc_tz_now(),
            response_time_ms=0,
            http_status=0,
            regexp_found=False,
            error=error
        )

    ts: datetime.datetime
    response_time_ms: NonNegativeInt
    http_status: NonNegativeInt
    regexp_found: bool
    error: str | None
