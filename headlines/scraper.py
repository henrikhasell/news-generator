import concurrent.futures
import hashlib
import json
import os
import re
import requests
import retry
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Optional


class ArticleError(Exception):
    pass


class Article:
    def __init__(
        self: object,
        url: str,
        title: str,
        date: datetime,
        content: str,
        related: List[str],
        category: str
    ):
        self.url = url
        self.title = title
        self.date = date
        self.content = content
        self.related = related
        self.category = category

    def hash(self: object) -> str:
        return hashlib.md5(json.dumps(self.json()).encode("utf-8")).hexdigest()[:10]

    def json(self: object) -> dict:
        return {
            'url': self.url(),
            'title': self.title,
            'date_published': self.date.isoformat(),
            'paragraphs': self.content.split('\n'),
            'category': self.category
        }

    def elastic_info(self: object) -> dict:
        return {
            'body': {
                'date_downloaded': datetime.now().isoformat(),
                'date_published': self.date.isoformat(),
                'category': self.category,
                'title': self.title
            },
            'id': self.url(),
            'index': 'articles'
        }


def stringify_soup(element):
    if element.string:
        return element.string
    return "".join(stringify_soup(child) for child in element.children)


def get_article_id_from_url(url: str) -> Optional[str]:
    match = re.match(r'.*/news/(.+-\d+.+?)', url)
    if match:
        return match.groups()[0]


def is_news_article(url: str) -> bool:
    return bool(get_article_id_from_url(url))


def create_directory_if_not_exist(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


@retry.retry(exceptions=requests.RequestException, tries=5)
def fetch_bbc_news_article(article_url: str) -> Article:
    result = requests.get(article_url)
    soup = BeautifulSoup(result.text, 'html.parser')

    paragraphs = soup.find_all("p")
    paragraphs_without_attributes = list(i for i in paragraphs if not i.attrs)

    date_attribute = 'data-seconds'

    all_dates_in_article = \
        [int(i.attrs[date_attribute]) for i in soup.findAll("div", {date_attribute: True})]

    if not all_dates_in_article:
        all_dates_in_article = \
            [int(i.attrs[date_attribute]) for i in soup.findAll("time", {date_attribute: True})]

    if len(all_dates_in_article) == 0:
        raise ArticleError(f"Could not find date in {article_url}")

    all_links_in_article = [a.attrs["href"] for a in soup.findAll("a", {"href": True})]

    article_title = soup.h1.text

    article_date = datetime.fromtimestamp(all_dates_in_article[0]) # Assuming the first date is the correct date.
    article_data = "\n".join(stringify_soup(item) for item in paragraphs_without_attributes)
    article_related = list(filter(is_news_article, all_links_in_article))

    article_category = soup.find("meta", {"property": "article:section"}).attrs['content']

    return Article(
        article_url,
        article_title,
        article_date,
        article_data,
        article_related,
        article_category
    )


@retry.retry(tries=5)
def post_news_article(article):
    article_json = article.json()
    response = requests.post(web_url, json=article_json)

    if response.status_code == 201:
        post_news_article_elasticsearch(article)


def save_news_article(article):
    directory_name = article.date.strftime("%y-%m-%d")
    file_name = f"{article.hash()}.txt"

    create_directory_if_not_exist(f"data/{directory_name}")

    with open(f"data/{directory_name}/{file_name}", "wb+") as file:
        file.write(article.content.encode("utf-8"))


def fetch_and_save_bbc_news_article(article_id):
    article = fetch_bbc_news_article(article_id)
    post_news_article(article)
    return article


def crawl(article_id: str):
    article = fetch_and_save_bbc_news_article(article_id)
    for related_article in article.related:
        crawl(related_article)


def crawl_concurrent(article_id):
    threads = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        def create_thread(_article_id, _threads, depth):
            article = fetch_and_save_bbc_news_article(_article_id)
            if depth < 10:
                for related_article_id in article.related:
                    _threads += [executor.submit(create_thread, related_article_id, _threads, depth+1)]

        create_thread(article_id, threads, 0)

        for thread in threads:
            thread.result()


if __name__ == "__main__":
    crawl_concurrent("uk-politics-50874389")
