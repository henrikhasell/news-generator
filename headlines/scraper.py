import concurrent.futures
import hashlib
import os
import re
import requests
import retry
from bs4 import BeautifulSoup
from datetime import datetime


web_url = os.environ.get('WEB_URL', 'http://localhost:5000/api/articles')


class ArticleError(Exception):
    pass


class Article:
    def __init__(self, id, title, date, content, related, category):
        self.id = id
        self.title = title
        self.date = date
        self.content = content
        self.related = related
        self.category = category

    def hash(self):
        return hashlib.md5(self.content.encode("utf-8")).hexdigest()[:10]

    def json(self):
        return {
            'url': f'https://www.bbc.co.uk/news/{self.id}',
            'title': self.title,
            'date_published': self.date.isoformat(),
            'paragraphs': self.content.split('\n'),
            'category': self.category
        }


def stringify_soup(element):
    if element.string:
        return element.string
    return "".join(stringify_soup(child) for child in element.children)


def get_article_id_from_string(string):
    match = re.match(".*/news/(.+-\d+.+?)", string)
    if match:
        return match.groups()[0]


def is_news_article(href):
    return bool(get_article_id_from_string(href))


def create_directory_if_not_exist(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


@retry.retry(tries=5)
def fetch_bbc_news_article(article_id):
    result = requests.get(f"https://www.bbc.co.uk/news/{article_id}")
    soup = BeautifulSoup(result.text, 'html.parser')

    paragraphs = soup.find_all("p")
    paragraphs_without_attributes = list(i for i in paragraphs if not i.attrs)

    date_attribute = 'data-seconds'

    all_dates_in_article = \
        [int(i.attrs[date_attribute]) for i in soup.findAll("div", {date_attribute: True})]

    if len(all_dates_in_article) == 0:
        raise ArticleError(f"Could not find date in {article_id}")

    all_links_in_article = [a.attrs["href"] for a in soup.findAll("a", {"href": True})]

    article_title = soup.h1.text

    article_date = datetime.fromtimestamp(all_dates_in_article[0]) # Assuming the first date is the correct date.
    article_data = "\n".join(stringify_soup(item) for item in paragraphs_without_attributes)
    article_related = list(get_article_id_from_string(a) for a in all_links_in_article if is_news_article(a))

    article_category = soup.find("meta", {"property": "article:section"}).attrs['content']

    return Article(
        article_id,
        article_title,
        article_date,
        article_data,
        article_related,
        article_category
    )


@retry.retry(tries=5)
def post_news_article(article):
    response = requests.post(web_url, json=article.json())


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


def crawl(article_id):
    article = fetch_and_save_bbc_news_article(article_id)
    for related_article in article.related:
        if related_article not in visited:
            visited.append(related_article)
            crawl(related_article)


def crawl_concurrent(article_id):
    threads = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        def create_thread(_article_id, _threads):
            article = fetch_and_save_bbc_news_article(_article_id)
            for related_article_id in article.related:
                if related_article_id not in visited:
                    _threads += [executor.submit(create_thread, related_article_id, _threads)]

        create_thread(article_id, threads)

        for thread in threads:
            thread.result()


visited = []

if __name__ == "__main__":
    crawl_concurrent("uk-politics-50874389")
