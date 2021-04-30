from flask_restplus import Namespace, fields


class SearchQueryDTO:
    api = Namespace('search', description='search operations')
    searchQuery = api.model('search', {
        'hashtag': fields.String(required=True, description='hashtag to search')
    })