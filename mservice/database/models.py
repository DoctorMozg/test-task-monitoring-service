import datetime

from pydantic import AnyUrl
from pydantic.dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MonitorModel:
    id: int
    url: AnyUrl
    regexp: str | None
    active: bool
    sync_interval: datetime.timedelta
    next_sync: datetime.datetime
