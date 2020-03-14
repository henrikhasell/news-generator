from datetime import datetime
from dateutil.rrule import DAILY, rrule
from retry import retry
import flask_sqlalchemy
import logging
import sqlalchemy
import timeago


db = flask_sqlalchemy.SQLAlchemy()


def relative_date(date):
    return timeago.format(date)


def serialise_date(date):
    return {
        'ddmmyy': date.strftime("%d/%m/%y"),
        'hhmmss': date.strftime("%H:%M:%S")
    }

def is_valid_attribute(attr):
    return attr not in ['metadata', 'query', 'query_class'] and not attr.startswith('_')


def get_model_attributes(model):
    return [i for i in dir(model) if is_valid_attribute(i)]


def serialise_attribute(attr, date_format):
    if type(attr) == datetime:
        return date_format(attr)
    return attr


def serialise_model(model, date_format=serialise_date):
    return {i: serialise_attribute(getattr(model, i), date_format) for i in get_model_attributes(model)}


class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String, unique=True)
    title = db.Column(db.String)
    category = db.Column(db.String)
    paragraphs = db.Column(db.JSON)
    date_published = db.Column(db.DateTime)
    date_added = db.Column(db.DateTime)


@retry(tries=3, delay=1)
def initialise(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()


def article_exists(url):
    article = Article.query.filter_by(url=url).one_or_none()
    return bool(article)


def add_article(article_json):
    if article_exists(article_json["url"]):
        return

    logging.info(f"Adding article {article_json['url']}")

    article = Article(
        url=article_json["url"],
        title=article_json["title"],
        category=article_json["category"],
        paragraphs=article_json["paragraphs"],
        date_published=article_json["date_published"],
        date_added=datetime.now()
    )

    result = {"title": article.title}

    try:
        db.session.add(article)
        db.session.commit()
        return_code = 201
    except sqlalchemy.exc.IntegrityError:
        db.session.rollback()
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
        .filter(Article.category.notin_(exclude_categories)).all()

    return [serialise_model(i) for i in articles]


def get_text(from_date, until_date, exclude_categories=[]):
    articles = get_articles(from_date, until_date, exclude_categories)
    paragraphs = []
    for article in articles:
        paragraphs += article["paragraphs"]
    return '\n'.join(paragraphs)
