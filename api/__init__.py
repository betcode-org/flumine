from flask import Flask
from flask_restful import (
    Api,
)

from api import config


app = Flask(__name__)
api = Api(app)
