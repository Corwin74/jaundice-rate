import asyncio
import ssl
import aiohttp
import certifi


async def fetch(session, url, ssl_context):
    async with session.get(url, ssl_context=ssl_context) as response:
        response.raise_for_status()
        return await response.text()


async def main():
    ssl_context = ssl.create_default_context(cafile=certifi.where())

    async with aiohttp.ClientSession() as session:
        html = await fetch(
            session,
            'http://inosmi.ru/20230322/kitay-261582482.html',
            ssl_context=ssl_context
        )
        print(html)


asyncio.run(main())
