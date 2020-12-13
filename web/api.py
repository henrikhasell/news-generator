import app
import flask
import flask_restx

import storage


blueprint = flask.Blueprint('api', __name__)

api = flask_restx.Api(
    blueprint,
    description='The interface for fetching and updating The Rabbit.',
    title='🐰 The Rabbit API',
    validate=True,
    version='1.0'
)


article_model = api.model('Article Post', {
    'url': flask_restx.fields.String(
        example='https://www.bbc.co.uk/news/uk-54194302',
        required=True
    ),
    'title': flask_restx.fields.String(
        example='Coronavirus: Test demand \'significantly outstripping\' capacity',
        required=True
    ),
    'category': flask_restx.fields.String(
        example='UK',
        required=True
    ),
    'paragraphs': flask_restx.fields.List(
        flask_restx.fields.String,
        example=['First paragraph.', 'Second paragraph.'],
        required=True
    ),
    'date_published': flask_restx.fields.DateTime(
        required=True
    )
})


@api.route('/articles')
class ArticleResource(flask_restx.Resource):
    @api.expect(article_model)
    def post(self):
        '''Post a new article.'''
        request_json = flask.request.json
        return storage.add_article(request_json)

    def get(self):
        '''Get all existing articles.'''
        return storage.get_all_articles()
