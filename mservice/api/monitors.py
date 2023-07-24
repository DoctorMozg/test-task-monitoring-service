import logging
from datetime import timedelta
from typing import Annotated

from asyncpg import Connection
from fastapi import APIRouter, Depends, Path
from pydantic import NonNegativeInt
from pydantic.dataclasses import dataclass
from pydantic_core import Url

from mservice.database.monitor_dao import MonitorDao
from mservice.schema.metrics import FrequencySec
from mservice.dependencies import db_connection

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/monitors', tags=['monitor'])


def monitor_dao(conn: Connection = Depends(db_connection)):
    return MonitorDao(conn)


@dataclass(frozen=True, slots=True)
class DeletionMessageResponse:
    message: str
    removed: bool


@dataclass(frozen=True, slots=True)
class CreatedItemMessageResponse:
    id: int


@dataclass(frozen=True, slots=True)
class UrlMonitorCreationRequest:
    url: str
    frequency_sec: FrequencySec
    regexp: str | None


@router.post('/', response_model=CreatedItemMessageResponse)
async def create(
    new_monitor: UrlMonitorCreationRequest,
    dao: MonitorDao = Depends(monitor_dao),
):
    monitor_id = await dao.create(
        Url(new_monitor.url),
        timedelta(seconds=new_monitor.frequency_sec),
        new_monitor.regexp
    )

    logger.info(
        f"Created a new URL monitor {new_monitor.url} with id {monitor_id}"
    )

    return CreatedItemMessageResponse(monitor_id)


@router.delete('/{id}/', response_model=DeletionMessageResponse)
async def delete(
        id: Annotated[NonNegativeInt, Path(title="ID of monitor for removal")],
        dao: MonitorDao = Depends(monitor_dao),
):
    is_removed = await dao.remove(id)

    message = (
        f"Disabled an URL monitor with id: {id}"
        if is_removed else
        f"Not found or already disabled an URL monitor with id: {id}"
    )

    logger.info(message)

    return DeletionMessageResponse(message, is_removed)
