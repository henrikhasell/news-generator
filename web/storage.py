from datetime import datetime, timezone

from dateutil.rrule import DAILY, rrule
import flask_sqlalchemy
import logging
import sqlalchemy
from retry import retry

import poem


db = flask_sqlalchemy.SQLAlchemy()


def serialise_date(date):
    return {
        'ddmmyy': date.strftime("%d/%m/%y"),
        'hhmmss': date.strftime("%H:%M:%S")
    }


def is_valid_attribute(attr):
    return attr not in {'metadata', 'query', 'query_class'} and not attr.startswith('_')


def get_model_attributes(model):
    return [i for i in dir(model) if is_valid_attribute(i)]


def serialise_attribute(attr, date_format):
    if type(attr) == datetime:
        return date_format(attr)
    return attr


def serialise_model(model, date_format=serialise_date):
    return {i: serialise_attribute(getattr(model, i), date_format) for i in get_model_attributes(model)}


class Article(db.Model):
    url = db.Column(db.String, primary_key=True)
    title = db.Column(db.String)
    category = db.Column(db.String)
    paragraphs = db.Column(db.JSON)
    date_published = db.Column(db.DateTime)
    date_added = db.Column(db.DateTime)


class Poem(db.Model):
    id = db.Column(db.String, primary_key=True)
    date_generated = db.Column(db.DateTime)
    paragraphs = db.Column(db.JSON)
    mode = db.Column(db.String)


def save_poem(poem):
    db_poem = Poem(
        id=poem.uuid,
        date_generated=poem.date_generated,
        paragraphs=poem.paragraphs,
        mode=poem.mode
    )
    logging.debug(f'Saving {poem.mode} article: {poem.uuid}')
    db.session.add(db_poem)
    db.session.commit()


def get_poem(uuid):
    db_poem = Poem.query.filter_by(id=uuid).one_or_none()
    if not db_poem:
        return
    return poem.Poem(
        db_poem.paragraphs,
        db_poem.date_generated,
        db_poem.mode,
        db_poem.id
    )


@retry(tries=3, delay=1)
def initialise(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()


def add_article(article_json):
    logging.info(f"Adding article {article_json['url']}")

    article = Article(
        url=article_json["url"],
        title=article_json["title"],
        category=article_json["category"],
        paragraphs=article_json["paragraphs"],
        date_published=article_json["date_published"],
        date_added=datetime.utcnow().replace(tzinfo=timezone.utc)
    )

    try:
        db.session.add(article)
        db.session.commit()
        result = 'Article sucessfully added.'
        return_code = 201
    except sqlalchemy.exc.IntegrityError:
        db.session.rollback()
        result = 'Article already exists.'
        return_code = 200

    return result, return_code


def get_all_articles():
    return [serialise_model(i) for i in Article.query.all()]


def get_distinct_categories():
    query = Article.query.with_entities(Article.category).distinct()
    query = query.all()
    query = [i[0] for i in query]
    query.sort()
    return query


def count_articles_by_category():
    categories = []
    for name in get_distinct_categories():
        count = Article.query.filter_by(category=name).count()
        categories += [{'name': name, 'count': count}]
    return categories


def count_articles_by_date_published(from_date, until_date, exclude_categories=[]):
    articles = Article.query \
        .filter(Article.date_published >= from_date) \
        .filter(Article.date_published <= until_date) \
        .filter(Article.category.notin_(exclude_categories)).all()

    result = {}

    for dt in rrule(DAILY, dtstart=from_date, until=until_date):
        string_time = dt.strftime("%Y-%m-%d")
        result[string_time] = 0

    for article in articles:
        string_time = article.date_published.strftime("%Y-%m-%d")
        result[string_time] += 1

    return result


def count_articles_by_date_added(from_date, until_date, exclude_categories=[]):
    articles = Article.query \
        .filter(Article.date_added >= from_date) \
        .filter(Article.date_added <= until_date) \
        .filter(Article.category.notin_(exclude_categories)).all()

    result = {}

    for dt in rrule(DAILY, dtstart=from_date, until=until_date):
        string_time = dt.strftime("%Y-%m-%d")
        result[string_time] = 0

    for article in articles:
        string_time = article.date_added.strftime("%Y-%m-%d")
        result[string_time] += 1

    return result


def get_articles_by_category(category):
    return [serialise_model(i) for i in
            Article.query.filter_by(category=category).order_by(Article.date_added.desc()).all()]


def get_article_by_id(article_id):
    article = Article.query.filter_by(id=article_id).first()
    return serialise_model(article) if article else None


def get_articles(from_date, until_date, exclude_categories=[]):
    articles = Article.query \
        .filter(Article.date_published >= from_date) \
        .filter(Article.date_published <= until_date) \
        .filter(Article.category.notin_(exclude_categories)) \
        .order_by(Article.date_published).all()

    return [serialise_model(i) for i in articles]


def get_text(from_date, until_date, exclude_categories=[]):
    articles = get_articles(from_date, until_date, exclude_categories)
    paragraphs = []
    for article in articles:
        paragraphs += article["paragraphs"]
    return '\n'.join(paragraphs)
