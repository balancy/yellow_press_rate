import asyncio

import aiofiles
import aiohttp
import pymorphy2

from adapters.inosmi_ru import sanitize
from text_tools import calculate_jaundice_rate, split_by_words


SITE_URL = 'https://inosmi.ru/20220302/ssha-253253195.html'
NEGATIVE_WORDS_PATH = 'charged_dict/negative_words.txt'
POSITIVE_WORDS_PATH = 'charged_dict/positive_words.txt'


async def fetch(session, url):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


async def get_file_content(filename):
    async with aiofiles.open(filename, 'r') as file:
        return await file.read()


async def main():
    morph = pymorphy2.MorphAnalyzer()

    async with aiohttp.ClientSession() as session:
        article_html = await fetch(session, SITE_URL)
        article_text = sanitize(article_html, plaintext=True)
        article_words = split_by_words(morph, article_text)

        negative_text = await get_file_content(NEGATIVE_WORDS_PATH)
        negative_words = split_by_words(morph, negative_text)

        positive_text = await get_file_content(POSITIVE_WORDS_PATH)
        positive_words = split_by_words(morph, positive_text)

        jaundice_rate = calculate_jaundice_rate(
            article_words,
            [*negative_words, *positive_words],
        )
        print(f'Рейтинг: {jaundice_rate}')
        print(f'Слов в статье: {len(article_words)}')


asyncio.run(main())
