from random import randint

import click
import httpx

TEMPLATES = [
    "https://jsonplaceholder.typicode.com/posts/",
    "https://jsonplaceholder.typicode.com/comments/",
    "https://jsonplaceholder.typicode.com/photos/",
    "https://jsonplaceholder.typicode.com/todos/",
    "https://jsonplaceholder.typicode.com/albums/",
]


@click.group()
def cli():
    pass


@cli.command()
@click.option(
    '--url', default="http://127.0.0.1:8000/monitors/", help='server URL'
)
@click.option(
    '--count', default=100, help='number of web monitors to generate per template'
)
def generate_monitors(url: str, count: int):
    click.echo('Starting template generation')

    for template in TEMPLATES:
        for i in range(count):
            result = httpx.post(
                url,
                json={
                    "url": f"{template}{i}",
                    "frequency_sec": randint(5, 30),
                    "regexp": ".*" if randint(0, 10) < 2 else None
                }
            )
            result.raise_for_status()

    click.echo('Finished template generation')


@cli.command()
def migrate():
    from mservice.dependencies import db_pool
    from mservice.database.migration import create_all_tables

    pool = await db_pool()
    async with pool.acquire() as conn:
        await create_all_tables(conn)


if __name__ == "__main__":
    cli()
