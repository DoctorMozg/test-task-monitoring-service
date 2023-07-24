import pytest

from mservice.parser import find_pattern


@pytest.mark.parametrize(
    'text, pattern, result',
    [
        pytest.param(
            'sample text',
            r'sample',
            True,
            id='basic',
        ),
        pytest.param(
            'sample text',
            r'[yu]+',
            False,
            id='basic not found',
        ),
        pytest.param(
            'sample text ' * 10000,
            r'[sample]+',
            True,
            id='huge string check',
        ),
        pytest.param(
            '',
            r'[yu]+',
            False,
            id='empty check',
            ),
    ]
)
@pytest.mark.asyncio
async def test_parser(text: str, pattern: str, result: bool):
    result_returned = await find_pattern(text, pattern)
    assert result_returned == result, "Found result must match"
