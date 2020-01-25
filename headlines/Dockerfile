FROM python:3.7

RUN pip install \
beautifulsoup4==4.8.1 \
requests==2.22.0 \
retry==0.9.2 \
sentry-sdk==0.14.1

WORKDIR /app

COPY headlines.py scraper.py ./

ENTRYPOINT ["sh", "-c", "while true; do python headlines.py; sleep $((60*60)); done"]
