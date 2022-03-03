import asyncio
from enum import Enum

import aiofiles
import aiohttp
import anyio
import pymorphy2

from adapters.inosmi_ru import sanitize
from text_tools import calculate_yellow_press_rate, split_by_words


NEGATIVE_WORDS_PATH = 'charged_dict/negative_words.txt'
POSITIVE_WORDS_PATH = 'charged_dict/positive_words.txt'
TEST_ARTICLES = [
    'https://inosmi.ru/20220303/kitay-shos-253268048.html',
    'https://inosmi.ru/20220302/ssha-253253195.html',
    'https://inosmi.ru/20220303/yadernoe-oruzhie-253265698.html',
    'https://inosmi.ru/20220303/ukraina-253269849.html',
    'https://inosmi.ru/20220303/torgovlya-253272049.html',
    'random',
]


class ProcessingStatus(Enum):
    OK = 'OK'
    FETCH_ERROR = 'FETCH_ERROR'


async def fetch(session, url):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


async def extract_file_content(filename):
    async with aiofiles.open(filename, 'r') as file:
        return await file.read()


async def gather_charged_words(morph):
    negative_text = await extract_file_content(NEGATIVE_WORDS_PATH)
    negative_words = split_by_words(morph, negative_text)

    positive_text = await extract_file_content(POSITIVE_WORDS_PATH)
    positive_words = split_by_words(morph, positive_text)

    return [*negative_words, *positive_words]


async def process_article(session, morph, charged_words, url, results):
    try:
        article_html = await fetch(session, url)
    except aiohttp.client_exceptions.InvalidURL:
        results.append(
            {
                'url': url,
                'status': ProcessingStatus.FETCH_ERROR.value,
                'rate': None,
                'words_count': None,
            }
        )
        return

    article_text = sanitize(article_html, plaintext=True)
    article_words = split_by_words(morph, article_text)

    rate = calculate_yellow_press_rate(article_words, charged_words)

    results.append(
        {
            'url': url,
            'status': ProcessingStatus.OK.value,
            'rate': rate,
            'words_count': len(article_words),
        }
    )


async def main():
    morph = pymorphy2.MorphAnalyzer()
    charged_words = await gather_charged_words(morph)
    results = []

    async with aiohttp.ClientSession() as session:
        async with anyio.create_task_group() as tg:
            for url in TEST_ARTICLES:
                tg.start_soon(
                    process_article,
                    session,
                    morph,
                    charged_words,
                    url,
                    results,
                )

    for result in results:
        print('URL:', result['url'])
        print('Status', result['status'])
        print('Rate:', result['rate'])
        print('Number of words:', result['words_count'])
        print()


asyncio.run(main())
