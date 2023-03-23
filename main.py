import asyncio
import ssl
import aiohttp
import aiofiles
from anyio import create_task_group
import certifi
import pymorphy2
from adapters.inosmi_ru import sanitize
from text_tools import split_by_words, calculate_jaundice_rate

TEST_ARTICLES = [
    'https://inosmi.ru/20230322/kitay-261582482.html',
    'https://inosmi.ru/20230323/ukraina-261622481.html',
    'https://inosmi.ru/20230323/konflikt-261628210.html',
    'https://inosmi.ru/20230323/lavra-261621781.html',
    'https://inosmi.ru/20230323/ssha-261613436.html',
    ]


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
    html = await fetch(
        session,
        url,
        ssl_context=ssl_context,
    )
    words = split_by_words(morph, sanitize(html, plaintext=True))
    rate = calculate_jaundice_rate(words, charged_words)
    words_count = len(words)
    results.append((title, rate, words_count))


async def main():
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
            title, rate, words_count = result
            print('Заголовок:', title)
            print(f'Рейтинг: {rate}\nКоличество слов: {words_count}')


asyncio.run(main())
