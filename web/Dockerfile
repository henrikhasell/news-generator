FROM python:3.7

RUN pip install \
python-dateutil==2.8.1 \
Flask==1.1.1 \
flask-restplus==0.13.0 \
Flask-SQLAlchemy==2.4.1 \
gunicorn==20.0.4 \
markovify==0.7.2 \
psycopg2==2.8.4 \
retry==0.9.2 \
timeago==1.0.13

WORKDIR /app

COPY api.py app.py poem.py storage.py ./
COPY templates ./templates

ENTRYPOINT ["gunicorn", "-b", "0.0.0.0:9000", "-w", "4", "app:app"]
