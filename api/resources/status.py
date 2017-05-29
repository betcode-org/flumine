from flask_restful import Resource

from api import config


class Status(Resource):

    def get(self):
        running = 'running' if config.trading._running else 'not running'
        return {
            'status': running,
            'streams': [],
            'stream_count': len(config.trading)
        }
