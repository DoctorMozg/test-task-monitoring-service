import logging

from asyncpg import Connection

logger = logging.getLogger(__name__)


async def create_all_tables(conn: Connection):
    logger.debug("Checking migration")
    async with conn.transaction():

        result = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1
                FROM pg_tables
                WHERE tablename = 'monitors'
            ) AS table_existence;
        """)
        if result:
            logger.debug("Skipping migration - tables are already there")
            return

        logger.debug("Executing migration")

        await conn.execute("""
            CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
        """)

        await conn.execute("""
        create table if not exists monitors
        (
            id serial constraint monitors_pk primary key,
            url text not null,
            regexp text,
            active boolean default true not null,
            sync_interval interval default '00:01:00'::interval not null,
            next_sync timestamp with time zone
                default CURRENT_TIMESTAMP not null
        );
        """)

        await conn.execute("""
        create index if not exists monitors_next_sync_index
            on monitors (next_sync);
        """)

        await conn.execute("""
        create table if not exists monitor_log
        (
            ts timestamptz not null,
            monitor_id integer not null
                constraint monitor_log_monitors_scan_fk references monitors,
            http_status integer not null,
            regexp_found boolean not null,
            response_time_ms integer not null,
            error text
        );
        """)

        await conn.execute("""
            SELECT create_hypertable(
                'monitor_log',
                'ts',
                 chunk_time_interval => interval '1 day'
             )
        """)
