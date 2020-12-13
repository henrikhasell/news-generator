FROM python:3.7

RUN pip install \
beautifulsoup4==4.8.1 \
requests==2.22.0 \
retry==0.9.2

WORKDIR /app

COPY __main__.py article.py crawler.py logger.py scraper.py utilities.py ./crawler/

ENTRYPOINT ["python", "-m", "crawler"]
