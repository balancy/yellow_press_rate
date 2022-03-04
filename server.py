from typing import Optional
from dataclasses import asdict

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from articles_handlers import process_articles


class TooManyUrlsException(Exception):
    pass


app = FastAPI()


@app.exception_handler(TooManyUrlsException)
async def exception_handler(request: Request, exc: TooManyUrlsException):
    return JSONResponse(
        status_code=400,
        content={'error': 'Too many urls in request, should be 10 or less'},
    )


@app.get('/')
async def read_root(urls: Optional[str]):
    urls = await process_articles(urls.split(','))
    if len(urls) > 10:
        raise TooManyUrlsException()

    urls_formatted = [asdict(url) for url in urls]
    return {"urls": urls_formatted}
