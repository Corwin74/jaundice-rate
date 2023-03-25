import asyncio
import time
import ssl
import logging
from enum import Enum
import aiohttp
import aiofiles
from anyio import create_task_group
from async_timeout import timeout
import certifi
import pymorphy2
from adapters.inosmi_ru import sanitize
from adapters.exceptions import ArticleNotFound
from text_tools import split_by_words, calculate_jaundice_rate, log_execution_time


logger = logging.getLogger('jandice_rate')


TEST_ARTICLES = [
    'https://inosmi.ru/20230322/kitay-261582482.html',
    'https://inosmi.ru/20230323/ukraina-261622481.html',
    'https://inosmi.ru/20230323/konflikt-261628210.html',
    'https://inosmi.ru/20230323/lavra-261621781.html',
    'https://inosmi.ru/20230323/ssha-261613436.html',
    'https://inosmi.ru/not/exist.html',
    'https://pikabu.ru/story/reklama_mvd_poka_ne_udalili_10071263',
]


class ProcessingStatus(Enum):
    OK = 'OK'
    FETCH_ERROR = 'FETCH_ERROR'
    PARSING_ERROR = 'PARSING_ERROR'
    TIMEOUT = 'TIMEOUT'

    def __str__(self):
        return str(self.value)


async def fetch(session, url, ssl_context):
    async with session.get(url, ssl_context=ssl_context) as response:
        response.raise_for_status()
        return await response.text()


async def process_article(
    session,
    ssl_context,
    morph,
    charged_words,
    url,
    title,
    results
):
    words = None
    rate = None
    words_count = None
    try:
        async with timeout(10):
            html = await fetch(
                session,
                url,
                ssl_context=ssl_context,
            )
        async with timeout(3):
            async with log_execution_time():
                words = await split_by_words(morph, sanitize(html, plaintext=True))
                rate = calculate_jaundice_rate(words, charged_words)
                words_count = len(words)
                status = ProcessingStatus.OK
    except aiohttp.ClientError:
        status = ProcessingStatus.FETCH_ERROR
    except ArticleNotFound:
        status = ProcessingStatus.PARSING_ERROR
    except asyncio.TimeoutError:
        status = ProcessingStatus.TIMEOUT
    results.append((title, status, rate, words_count))


async def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    ssl_context = ssl.create_default_context(cafile=certifi.where())

    async with aiohttp.ClientSession() as session:
        morph = pymorphy2.MorphAnalyzer()
        charged_words = []
        async with aiofiles.open(
            'charged_dict/negative_words.txt',
            mode='r'
        ) as f:
            async for line in f:
                charged_words.append(line.rstrip())
        results = []
        async with create_task_group() as tg:
            for url in TEST_ARTICLES:
                title = url
                tg.start_soon(
                    process_article,
                    session,
                    ssl_context,
                    morph,
                    charged_words,
                    url,
                    title,
                    results
                )

        for result in results:
            title, status, rate, words_count = result
            print(5*'=')
            print('Заголовок:', title)
            print(f'Статус: {status}')
            print(f'Рейтинг: {rate}\nКоличество слов: {words_count}')


asyncio.run(main())
