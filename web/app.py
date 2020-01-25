import flask
import os
import api
import poem
import sentry_sdk
import storage

sentry_dsn = os.environ.get("WEB_SENTRY_DSN", None)

if sentry_dsn:
    sentry_sdk.init(sentry_dsn)

app = flask.Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", 'postgres://user:user@localhost')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['RESTPLUS_VALIDATE '] = True
app.register_blueprint(api.blueprint, url_prefix='/api')
storage.initialise(app)


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


@app.route("/", defaults={"mode": "all"})
@app.route("/<mode>")
def index(mode):
    poem_generator = poem.PoemGenerator()
    if mode not in ['all', 'this_month', 'this_year', 'today']:
        flask.abort(404)
    mode_description = {
        'all': None,
        'this_month': "This poem was generated from this month's news.",
        'this_year': "This poem was generated from this year's news.",
        'today': "This poem was generated from today's news."
    }
    return flask.render_template(
        "index.html",
         mode_description=mode_description[mode],
         poem=poem_generator.generate_poem())
