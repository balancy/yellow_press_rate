# Yellow press filter

The web application allows the analysis of the requested articles for the presence of charged words which can be a sign of yellow press.

At the moment it supports only [ИНОСМИ.РУ](https://inosmi.ru/) site. It was developed a special adapter for this site that extracts the plain text from the rest of the HTML content. Other news sites will require new adapters. It's possible to create a universal adapter that could work with all news sites, but its development could be time-consuming.

After plain text extraction, the app divide texts into separate words, cast them to normal form, and check against a list of charged words.


# Install

You'll need at least python3.7 and poetry.

Clone the repository

```bash
git clone https://github.com/balancy/yellow_press_rate.git
```

Go inside the cloned repository, activate the virtual environment and install dependencies.

```bash
poetry shell
```

```bash
poetry install
```

# Launch

```shell
uvicorn server:app
```

The app will be available via [http://127.0.0.1:8000]().

In order to analyse the articles, you'll need to pass them as get parameters, divided by a comma.

Example:

[http://127.0.0.1:8000/?urls=https://inosmi.ru/20220303/kitay-shos-253268048.html,https://another_article]()


# Launch tests

The library [pytest](https://docs.pytest.org/en/latest/) is used.

```
python -m pytest adapters/inosmi_ru.py
```

```
python -m pytest text_tools.py
```

```
python -m pytest articles_handlers.py
```
