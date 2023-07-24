import asyncio
import logging

from mservice.scheduler import monitors_update_task
from mservice.utils import prepare_logger

logger = logging.getLogger(__name__)


async def main():
    prepare_logger()
    logger.info("Starting monitoring worker")
    await monitors_update_task()
    logger.info("Stopping monitoring worker")


if __name__ == "__main__":
    asyncio.run(main())
