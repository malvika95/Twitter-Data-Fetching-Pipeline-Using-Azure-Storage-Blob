#Author : Malvika Mohan
#Date : 3rd April, 2021

from flask_restplus import Api
from flask import Blueprint
from flask_restplus import reqparse


from .main.controller.fetch_tweet_controller import api as searchns

blueprint = Blueprint('api', __name__)

api = Api(blueprint,
          title='FLASK RESTPLUS API',
          version='1.0',
          description='a boilerplate for flask restplus web service'
          )
# parser = reqparse.RequestParser()
# parser.add_argument('query', required=True, help="Query cannot be blank!")
api.add_namespace(searchns, path='/search')
