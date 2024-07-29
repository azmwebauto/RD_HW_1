import argparse
import asyncio
import pathlib
from typing import Iterable
from urllib.parse import urlparse

import httpx

import logging
import functools

logging.basicConfig(level=logging.INFO)

TIMEOUT = 10
RESULTS_FOLDER = pathlib.Path('results')
if not RESULTS_FOLDER.exists():
    RESULTS_FOLDER.mkdir()


async def get_response(client, url: str) -> tuple[str, httpx.Response] | tuple[str, Exception]:
    try:
        async with asyncio.timeout(TIMEOUT):
            response = await client.get(url)
            return url, response
    except Exception as e:
        logging.error(f'{url}: {e}')
        return url, e


async def parse_urls(urls: Iterable[str]):
    async with httpx.AsyncClient() as client:
        get_response_partial = functools.partial(get_response, client)
        tasks = [asyncio.create_task(get_response_partial(url)) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    for url, result in results:
        if isinstance(result, Exception):
            continue
        logging.info(f'{url}: {len(result.content)=}')
        with open(pathlib.Path('results', urlparse(url).hostname), 'w') as f:
            f.write(result.text)


async def main():
    arguments_parser = argparse.ArgumentParser()
    arguments_parser.add_argument('--file', '-f', required=True, type=str)
    args = arguments_parser.parse_args()

    with open(args.file, 'r') as f:
        urls = f.read().splitlines()

    await parse_urls(urls)


if __name__ == '__main__':
    asyncio.run(main())
