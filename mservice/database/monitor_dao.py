import datetime
import re
from dataclasses import dataclass
from datetime import timedelta

from asyncpg import Connection
from pydantic import validate_call, AnyUrl, NonNegativeInt, PositiveInt

from mservice.database.models import MonitorModel
from mservice.schema.metrics import SiteMetricSchema


class WrongRegexException(Exception):
    pass


@dataclass
class MonitorDao:

    INSERT = """
        INSERT INTO
            monitors (url, regexp, sync_interval)
            VALUES ($1, $2, $3)
        RETURNING id
    """

    DELETE = """
        UPDATE monitors SET
            active = FALSE
            WHERE id = $1 AND active
        RETURNING id
    """

    SELECT_BY_ID = """
        SELECT * FROM monitors
            WHERE id = $1 AND active
    """

    SELECT_UNLOCKED = """
        SELECT * FROM monitors
            WHERE
                next_sync <= $1
                AND active
        ORDER BY next_sync
            LIMIT $2
        FOR UPDATE
        SKIP LOCKED
    """

    RESCHEDULE = """
        UPDATE monitors SET
            next_sync = CURRENT_TIMESTAMP + sync_interval
        WHERE id = any($1::integer[])
            AND active
        RETURNING *
    """

    COUNT_ACTIVE = """
        SELECT COUNT(*) FROM monitors WHERE active
    """

    INSERT_LOG = """
        INSERT INTO
            monitor_log (
                monitor_id, ts, http_status, response_time_ms, regexp_found, error
            )
            VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING scan
    """

    connection: Connection

    @staticmethod
    def _db_to_model(row) -> MonitorModel:
        return MonitorModel(**row)

    @validate_call
    async def create(
            self, url: AnyUrl, interval: timedelta, regexp: str | None
    ) -> int:
        if regexp is not None:
            try:
                re.compile(regexp)
            except Exception as e:
                raise WrongRegexException(
                    f"Failed to compile RegExp: {regexp}"
                ) from e

        id = await self.connection.fetchval(
            self.INSERT,
            str(url), regexp, interval
        )

        return id

    @validate_call
    async def remove(
            self, id: NonNegativeInt
    ) -> bool:
        removed_id = await self.connection.fetchval(
            self.DELETE, id
        )

        return removed_id is not None

    @validate_call
    async def reschedule(
            self, ids: list[NonNegativeInt]
    ):
        rescheduled_list = await self.connection.fetch(
            self.RESCHEDULE, ids
        )

        return [self._db_to_model(row) for row in rescheduled_list]

    @validate_call
    async def select_unlocked(
            self, execute_before: datetime.datetime, limit: PositiveInt
    ) -> list[MonitorModel]:
        unlocked_list = await self.connection.fetch(
            self.SELECT_UNLOCKED, execute_before, limit
        )

        return [self._db_to_model(row) for row in unlocked_list]

    async def count(self) -> int:
        return await self.connection.fetchval(self.COUNT_ACTIVE)

    @validate_call
    async def create_log_items_from_schema(
            self, items: list[tuple[int, SiteMetricSchema]]
    ) -> int:
        monitor_id = await self.connection.executemany(
            self.INSERT_LOG,
            [
                (
                    monitor_id,
                    item.ts,
                    item.http_status,
                    item.response_time_ms,
                    item.regexp_found,
                    item.error
                )
                for monitor_id, item in items
            ]
        )

        return monitor_id
