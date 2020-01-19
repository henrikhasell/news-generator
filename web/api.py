import flask
import flask_restplus
import storage

blueprint = flask.Blueprint('api', __name__)
api = flask_restplus.Api(blueprint)


article_model = api.model('Article', {
    'url': flask_restplus.fields.String(required=True),
    'title': flask_restplus.fields.String(required=True),
    'category': flask_restplus.fields.String(required=True),
    'paragraphs': flask_restplus.fields.List(flask_restplus.fields.String, required=True),
    'date_published': flask_restplus.fields.DateTime(dt_format='iso8601', required=True)
})


@api.route('/articles')
class ArticleResource(flask_restplus.Resource):
    @api.expect(article_model, validate=True)
    def post(self):
        request_json = flask.request.json
        return storage.add_article(request_json)

    def get(self):
        return storage.get_all_articles()
