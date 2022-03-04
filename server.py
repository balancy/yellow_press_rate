from typing import Optional
from dataclasses import asdict

from fastapi import FastAPI

from main import analyse_articles

TEST_ARTICLES = [
    'https://inosmi.ru/20220303/kitay-shos-253268048.html',
    'https://inosmi.ru/20220302/ssha-253253195.html',
    'https://inosmi.ru/20220303/yadernoe-oruzhie-253265698.html',
    'https://inosmi.ru/20220303/ukraina-253269849.html',
    'https://inosmi.ru/20220303/torgovlya-253272049.html',
    'https://random.random/random.html',
    'https://lenta.ru/brief/2021/08/26/afg_terror/',
    'just_some_phrase',
]

app = FastAPI()


@app.get('/')
async def read_root(urls: Optional[str]):
    # http://127.0.0.1:8000/?urls=https://inosmi.ru/20220303/kitay-shos-253268048.html,random,https://lenta.ru/brief/2021/08/26/afg_terror/
    urls = await analyse_articles(urls.split(','))
    urls_formatted = [asdict(url) for url in urls]
    return {"urls": urls_formatted}
