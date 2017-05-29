from flask_restful import Resource

from .. import config


class Settings(Resource):

    def get(self):
        return config.SETTINGS
