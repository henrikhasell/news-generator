import os

import requests

from .crawler import Crawler


if __name__ == '__main__':
    crawler = Crawler([
        'https://www.bbc.co.uk/news/uk',
        'https://www.bbc.co.uk/news/world',
        'https://www.bbc.co.uk/news/business',
        'https://www.bbc.co.uk/news/politics',
        'https://www.bbc.co.uk/news/technology',
        'https://www.bbc.co.uk/news/science_and_environment',
        'https://www.bbc.co.uk/news/health',
        'https://www.bbc.co.uk/news/education',
        'https://www.bbc.co.uk/news/entertainment_and_arts'
    ])
    for article in crawler.crawl():
        requests.post(os.environ['WEB_URL'], json=article.json())