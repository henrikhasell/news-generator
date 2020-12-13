import re
from urllib.parse import urlparse


def is_news_article(url: str) -> bool:
    return bool(re.match(r'^/news/(.+-\d+.+?)', urlparse(url).path))