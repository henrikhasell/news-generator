import flask
import logging
import os
import calendar_render
import poem
import api
import sentry_sdk
import storage
from datetime import datetime


logging_level = os.environ.get("LOGGING_LEVEL", None)
sentry_dsn = os.environ.get("WEB_SENTRY_DSN", None)

if logging_level:
    logging.basicConfig(level=logging_level)

if sentry_dsn:
    sentry_sdk.init(sentry_dsn)

app = flask.Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", 'postgres://user:user@localhost')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['RESTPLUS_VALIDATE '] = True
app.register_blueprint(api.blueprint, url_prefix='/api')
storage.initialise(app)


with app.app_context():
    poem_generator = poem.PoemGenerator()


@app.route("/categories")
def category():
    categories = storage.count_articles_by_category()
    selected_category = flask.request.args.get("category") or "UK Politics"
    articles = storage.get_articles_by_category(selected_category)
    return flask.render_template(
        "categories.html",
        selected_category=selected_category,
        categories=categories,
        articles=articles
    )


@app.route("/article/<article_id>")
def article(article_id):
    article = storage.get_article_by_id(article_id)
    if not article:
        flask.abort(404)
    return flask.render_template("article.html", article=article)


@app.route("/poem/<uuid>")
def poem(uuid):
    poem=storage.get_poem(uuid)
    title_dict = {
        'today': 'Poem of the Day',
        'this_month': 'Poem of the Month',
        'this_year': 'Poem of the Year'
    }
    if not poem:
        flask.abort(404)

    return flask.render_template(
        "poem.html",
        poem=poem,
        title=title_dict[poem.mode]
    )


@app.route("/calendar", defaults={"year": 2020})
@app.route("/calendar/<int:year>")
def calendar_year(year):
    return flask.render_template(
        "calendar_year.html",
        table_json=calendar_render.articles_published_by_year(year)
    )


@app.route("/calendar/<int:year>/<int:month>", defaults={"day": None})
@app.route("/calendar/<int:year>/<int:month>/<int:day>")
def calendar_month(year, month, day):
    if day:
        from_date = datetime(year, month, day)
        until_date = datetime(year, month, day + 1)

        articles = storage.get_articles(from_date, until_date)
    else:
        articles = None

    return flask.render_template(
        "calendar.html",
        articles=articles,
        table_json=calendar_render.articles_published_calendar(year, month),
        title=datetime(year, month, 1).strftime('%B %Y'))


@app.route("/about")
def about():
    return flask.render_template("about.html")


@app.route("/")
def index():
    return flask.render_template(
        "index.html",
         poem_of_the_day=poem_generator.generate_poem('today'),
         poem_of_the_month=poem_generator.generate_poem('this_month'),
         poem_of_the_year=poem_generator.generate_poem('this_year'))


@app.route("/poem")
def get_poem():
    return flask.jsonify(poem_generator.generate_poem('today').paragraphs)
