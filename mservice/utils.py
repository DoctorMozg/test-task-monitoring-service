import datetime
import logging

from mservice import settings


def utc_tz_now() -> datetime.datetime:
    return datetime.datetime.now(tz=datetime.timezone.utc)


def prepare_logger():
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format='%(asctime)s %(name)s %(levelname)s: %(message)s'
    )
