from scraper import ArticleError, fetch_and_save_bbc_news_article, get_article_id_from_string, is_news_article
from bs4 import BeautifulSoup
import concurrent.futures
import requests

news_categories = [
    'https://www.bbc.co.uk/news/uk',
    'https://www.bbc.co.uk/news/world',
    'https://www.bbc.co.uk/news/business',
    'https://www.bbc.co.uk/news/politics',
    'https://www.bbc.co.uk/news/technology',
    'https://www.bbc.co.uk/news/science_and_environment',
    'https://www.bbc.co.uk/news/health',
    'https://www.bbc.co.uk/news/education',
    'https://www.bbc.co.uk/news/entertainment_and_arts'
]


def get_all_articles_at_url(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    all_anchors_in_article = soup.find_all('a')
    hrefs = [i.attrs['href'] for i in all_anchors_in_article]
    return [get_article_id_from_string(i) for i in hrefs if is_news_article(i)]


def save_all_articles_at_url(url):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        threads = []
        for article_id in get_all_articles_at_url(url):
            threads += [executor.submit(fetch_and_save_bbc_news_article, article_id)]
        for thread in threads:
            try:
                thread.result()
            except ArticleError as e:
                print(e)


def fetch_and_save_headlines():
    with concurrent.futures.ThreadPoolExecutor() as executor:
        threads = []

        for news_category in news_categories:
            threads += [executor.submit(save_all_articles_at_url, news_category)]

        for thread in threads:
            thread.result()


if __name__ == '__main__':
    fetch_and_save_headlines()

