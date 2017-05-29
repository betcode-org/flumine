import json
from flask import Flask
from flask_restful import (
    Api,
)

from flumine import Flumine
from api.resources import (
    Settings,
    Status,
)
from api import config


# load settings
with open('flumine_settings.json') as data_file:
    config.SETTINGS = json.load(data_file)

# create flumine
config.trading = Flumine(
    settings=config.SETTINGS,
)


app = Flask(__name__)
api = Api(app)


api.add_resource(Settings, '/api/settings')
api.add_resource(Status, '/api/status')
