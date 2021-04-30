import random
from flask import request, make_response, jsonify
from flask_restplus import Resource
from ..util.dto import SearchQueryDTO
from ..service.fetch_tweets_2 import TweetLoader

api = SearchQueryDTO.api
searchQuery = SearchQueryDTO.searchQuery


@api.route('/')
class SearchHandler(Resource):

    @api.expect(searchQuery)
    def post(self):
        tweet_loader = TweetLoader()
        json_data = request.json
        search_query = json_data['hashtag']
        tweet_loader.load_auth_details('app/main/service/resources/keys.json')
        request_id = "request_" + str(random.randint(1000, 9999))
        message_list = tweet_loader.load_params('app/main/service/resources/config.json',str(search_query), request_id)
        if len(message_list):
            response = make_response(
                jsonify(
                    {
                        "Status" : "Error",
                        "Message" : message_list
                    }
                ),
                500
            )
        else :
            response = make_response(
                jsonify(
                    {"Status": "Success",
                     "Message" : "Your data is being loaded",
                     "request_id" : request_id}
                ),
                200,
            )
        return response
