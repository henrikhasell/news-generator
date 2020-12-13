from typing import List, Optional
from urllib.parse import urlparse

import bs4
import requests
from datetime import datetime, timezone
from retry import retry

from .article import Article
from .utilities import is_news_article


class ScraperError(Exception):
    pass



def _stringify_soup(element: bs4.element.PageElement) -> str:
    if element.text:
        return element.text
    return "".join(_stringify_soup(child) for child in element.children)


class Scraper:
    date_formats = [
        r'%Y-%m-%dT%H:%M:%S.%fZ',
        r'%Y-%m-%dT%H:%M:%S+%f',
        r'%Y-%m-%dT%H:%M:%SZ'
    ]

    @staticmethod
    @retry(exceptions=requests.RequestException, tries=5, delay=1)
    def fetch_article(url: str) -> requests.Response:
        return requests.get(url)

    def __init__(self: object, url: str):
        result = Scraper.fetch_article(url)
        result.encoding = result.apparent_encoding
        self.soup = bs4.BeautifulSoup(result.text, 'html.parser')
        self.url = urlparse(url)

    def _format_href(self: object, href: str) -> str:
        if href.startswith('/'):
            return f'{self.url.scheme}://{self.url.hostname}{href}'
        
        url = urlparse(href)
        return f'{url.scheme}://{url.hostname}{url.path}'

    def get_title(self: object) -> str:
        return self.soup.h1.text

    def get_date(self: object) -> datetime:
        date_element = self.soup.find('time', {'datetime': True})

        if not date_element:
            raise ScraperError(f'Could not find date in article {self.url.path}')

        date_string = date_element['datetime']

        for date_format in self.date_formats:
            try:
                return datetime.strptime(date_string, date_format)\
                    .replace(tzinfo=timezone.utc)
            except ValueError:
                pass

        raise ScraperError(f'Unrecognized date format {date_string}')

    def get_related(self: object) -> List[str]:
        hrefs = self.soup.find_all('a', {'href': True})
        hrefs = list(filter(is_news_article, [i['href'] for i in hrefs]))
        return [self._format_href(i) for i in hrefs]

    def get_content(self: object) -> List[str]:
        article_paragraphs = self.soup.find_all('p')
        article_paragraphs = filter(lambda i: not i.attrs, article_paragraphs)
        return [_stringify_soup(i) for i in article_paragraphs]

    def get_category(self: object) -> str:
        return self.soup.find('meta', {'property': 'article:section'}).attrs['content']