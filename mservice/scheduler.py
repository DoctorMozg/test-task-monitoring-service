import asyncio
import logging
import time
from asyncio import CancelledError

from asyncpg import Connection

from mservice import settings
from mservice.database.base import create_connection
from mservice.database.models import MonitorModel
from mservice.database.monitor_dao import MonitorDao
from mservice.parser import find_pattern
from mservice.requester import request_url, RequestFailedSchema
from mservice.schema.metrics import SiteMetricSchema
from mservice.utils import utc_tz_now

logger = logging.getLogger(__name__)


async def _sync_item(item: MonitorModel) -> tuple[int, SiteMetricSchema]:
    """
    Makes a request to the server and returns a populated metric.
    :param item: monitor to work with
    :return: populated metric
    """
    request_result = await request_url(item.url)
    request_time = utc_tz_now()

    if isinstance(request_result, RequestFailedSchema):
        return item.id, SiteMetricSchema.from_error(request_result.error)

    regexp_found = (
        False
        if item.regexp is None
        else find_pattern(request_result.body, item.regexp)
    )

    response_time_ms = round(request_result.response_time.total_seconds() * 1000)
    scan_result_item = SiteMetricSchema(
        ts=request_time,
        response_time_ms=response_time_ms,
        http_status=request_result.http_status,
        regexp_found=regexp_found,
        error=None
    )

    return item.id, scan_result_item


async def _sync_batch(connection: Connection) -> int:
    """
    Runs one batch of monitors, persists collected metrics and reschedules
    monitors for the next run.
    Uses settings.BATCH_FETCH_AMOUNT in order to determine size of the batch.
    :param connection: database connection
    :return: amount of updated items
    """
    async with connection.transaction():
        mdao = MonitorDao(connection)

        unlocked_items = await mdao.select_unlocked(settings.BATCH_FETCH_AMOUNT)

        if len(unlocked_items) == 0:
            logger.info("No items to sync - skipping")

        logger.info(f"Syncing {len(unlocked_items)} monitors")

        results = await asyncio.gather(
            *[_sync_item(item) for item in unlocked_items]
        )

        await mdao.create_log_items_from_schema(results)

        await mdao.reschedule([item.id for item in unlocked_items])

        logger.info("Sync finished")

    return len(unlocked_items)


async def monitors_update_task():
    """
    Task for periodical monitor updates.
    Uses only one connection. Can be furter
    """
    connection = await create_connection()

    try:
        while True:
            task_start_time = time.time()
            logger.debug("Starting a new monitor sync cycle")
            while (sync_count := await _sync_batch(connection)) > 0:
                logger.debug(f"Synced {sync_count} items")
            task_elapsed_time = time.time() - task_start_time
            logger.debug(
                f"Finishing monitor sync cycle "
                f"(it took {task_elapsed_time} seconds)"
            )

            if sync_count >= settings.BATCH_FETCH_AMOUNT:
                logger.debug("Skipping waiting - max amount")
            if task_elapsed_time < settings.POLL_INTERVAL:
                sleep_time = settings.POLL_INTERVAL - task_elapsed_time
                logger.debug(f"Going to sleep for {sleep_time} seconds")
                await asyncio.sleep(sleep_time)
    except CancelledError:
        logger.info("The task is cancelled - application is aborting")
        await connection.close()
