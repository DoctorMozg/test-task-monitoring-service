import re


def find_pattern(source: str, regexp: str) -> bool:
    """
    Searches source for regexp.

    WARNING. Python regexp support is quite slow, but assuming there won't be
    tens of thousands of chars to search in it is fast enough for async
    environment. In other cases multiprocessing should be considered.

    :param source: source text to search in
    :param regexp: search request
    :return: True if found any items
    """
    return re.search(regexp, source, re.MULTILINE) is not None
