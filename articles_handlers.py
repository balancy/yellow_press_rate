import asyncio
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from time import perf_counter
from typing import Optional

import aiofiles
import aiohttp
import anyio
import async_timeout
import pymorphy2
import pytest

from adapters.inosmi_ru import sanitize
from adapters.exceptions import ArticleNotFound
from text_tools import calculate_yellow_press_rate, split_by_words


NEGATIVE_WORDS_PATH = 'charged_dict/negative_words.txt'
POSITIVE_WORDS_PATH = 'charged_dict/positive_words.txt'
TIMEOUT = 3


class ProcessingStatus(Enum):
    OK = 'OK'
    FETCH_ERROR = 'FETCH_ERROR'
    PARSE_ERROR = 'PARSE_ERROR'
    TIMEOUT_ERROR = 'TIMEOUT_ERROR'


@dataclass
class ArticleAnalyseStats:
    url: str
    status: str
    rate: Optional[float] = None
    words_count: Optional[int] = None


@contextmanager
def timeit() -> float:
    start = perf_counter()
    yield lambda: perf_counter() - start


async def fetch(session, url):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


async def extract_file_content(filename):
    async with aiofiles.open(filename, 'r') as file:
        return await file.read()


async def gather_charged_words(morph):
    negative_text = await extract_file_content(NEGATIVE_WORDS_PATH)
    negative_words = await split_by_words(morph, negative_text)

    positive_text = await extract_file_content(POSITIVE_WORDS_PATH)
    positive_words = await split_by_words(morph, positive_text)

    return [*negative_words, *positive_words]


async def process_article(
    session, morph, charged_words, url, results, timeout=TIMEOUT
):
    try:
        article_html = await fetch(session, url)
        article_text = sanitize(article_html, plaintext=True)
        async with async_timeout.timeout(timeout):
            article_words = await split_by_words(morph, article_text)

    except aiohttp.ClientError:
        stats = ArticleAnalyseStats(url, ProcessingStatus.FETCH_ERROR.value)

    except asyncio.TimeoutError:
        stats = ArticleAnalyseStats(url, ProcessingStatus.TIMEOUT_ERROR.value)

    except ArticleNotFound:
        stats = ArticleAnalyseStats(url, ProcessingStatus.PARSE_ERROR.value)

    else:
        rate = calculate_yellow_press_rate(article_words, charged_words)
        stats = ArticleAnalyseStats(
            url, ProcessingStatus.OK.value, rate, len(article_words)
        )

    finally:
        results.append(stats)


async def process_articles(urls):
    morph = pymorphy2.MorphAnalyzer()
    charged_words = await gather_charged_words(morph)
    results = []

    async with aiohttp.ClientSession() as session:
        async with anyio.create_task_group() as tg:
            for url in urls:
                tg.start_soon(
                    process_article,
                    session,
                    morph,
                    charged_words,
                    url,
                    results,
                )

    return results


@pytest.mark.asyncio
async def test_process_article():
    morph = pymorphy2.MorphAnalyzer()
    charged_words = await gather_charged_words(morph)

    async with aiohttp.ClientSession() as session:
        url = 'https://lenta.ru/brief/2021/08/26/afg_terror/'
        results = []
        await process_article(session, morph, charged_words, url, results)
        [stats] = results

        assert stats == ArticleAnalyseStats(
            url,
            ProcessingStatus.PARSE_ERROR.value,
        )

        url = 'https://inosmi.ru/20220303/kitay-shos-253268048.html'
        results = []
        await process_article(session, morph, charged_words, url, results, 0.2)
        [stats] = results
        assert stats == ArticleAnalyseStats(
            url,
            ProcessingStatus.TIMEOUT_ERROR.value,
        )

        url = 'random_link'
        results = []
        await process_article(session, morph, charged_words, url, results)
        [stats] = results

        assert stats == ArticleAnalyseStats(
            url,
            ProcessingStatus.FETCH_ERROR.value,
        )
