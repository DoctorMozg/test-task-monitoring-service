import asyncio
import re
from concurrent.futures import ProcessPoolExecutor

from mservice import settings

process_executor = ProcessPoolExecutor()


def find_pattern_sync(source: str, regexp: str) -> bool:
    return re.match(regexp, source) is not None


async def find_pattern(source: str, regexp: str) -> bool:
    if len(source) > settings.SEPARATE_REGEX_PARSE_MIN_SIZE:
        return await asyncio.get_event_loop().run_in_executor(
            process_executor, find_pattern_sync, source, regexp
        )

    return find_pattern_sync(source, regexp)
