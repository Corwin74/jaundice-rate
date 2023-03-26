import asyncio
import ssl
import logging
from enum import Enum
import aiohttp
from aiohttp import web
from anyio import create_task_group
from async_timeout import timeout
import certifi
import pymorphy2
from adapters.inosmi_ru import sanitize
from adapters.exceptions import ArticleNotFound, TooManyUrls
from text_tools import (
    split_by_words, calculate_jaundice_rate, log_execution_time
)


logger = logging.getLogger('jandice_rate')


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
    results,
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
                words = await split_by_words(
                    morph,
                    sanitize(html, plaintext=True),
                )
                rate = calculate_jaundice_rate(words, charged_words)
                words_count = len(words)
                status = ProcessingStatus.OK
    except aiohttp.ClientError:
        status = ProcessingStatus.FETCH_ERROR
    except ArticleNotFound:
        status = ProcessingStatus.PARSING_ERROR
    except asyncio.TimeoutError:
        status = ProcessingStatus.TIMEOUT
    results.append((url, status, rate, words_count))


async def handle_get(request):
    try:
        urls = request.rel_url.query['urls']
        urls = urls.split(',')
        if len(urls) > 10:
            raise TooManyUrls()
        async with aiohttp.ClientSession() as session:
            results = []
            async with create_task_group() as tg:
                for url in urls:
                    tg.start_soon(
                        process_article,
                        session,
                        request.app['ssl_context'],
                        request.app['morph'],
                        request.app['charged_words'],
                        url,
                        results
                    )
        response = []
        for result in results:
            url, status, rate, words_count = result
            response.append(
                {
                    'status': repr(status),
                    'url': url,
                    'score': rate,
                    'word_count': words_count,
                }
            )
        return web.json_response(response)
    except KeyError:
        return web.json_response(
            {'error': 'urls parameter not found in request'},
            status=400,
        )
    except TooManyUrls:
        return web.json_response(
            {'error': 'too many urls in request, should be 10 or less'},
            status=400,
        )


def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    app = web.Application()
    app.add_routes([web.get('/', handle_get)])

    charged_words = []
    with open('charged_dict/negative_words.txt', mode='r') as f:
        for line in f:
            charged_words.append(line.rstrip())
    app['charged_words'] = charged_words
    app['ssl_context'] = ssl.create_default_context(cafile=certifi.where())
    app['morph'] = pymorphy2.MorphAnalyzer()

    web.run_app(app)


if __name__ == '__main__':
    main()
