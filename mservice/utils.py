import datetime
import logging

from mservice import settings


def utc_tz_now() -> datetime.datetime:
    """
    :return: Current time with UTC tz set
    """
    return datetime.datetime.now(tz=datetime.timezone.utc)


def prepare_logger():
    """
    Sets logger format and level.
    """
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format='%(asctime)s %(name)s %(levelname)s: %(message)s'
    )
