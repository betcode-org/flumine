import json
from flask_restful import (
    Resource,
    abort,
    reqparse,
)

from api.utils import create_short_uuid
from api import config
from flumine import Flumine


# load settings
with open('flumine_settings.json') as data_file:
    config.SETTINGS = json.load(data_file)

# stream data
STREAMS = {}
FLUMINES = {}


def abort_if_stream_doesnt_exist(stream_id):
    if stream_id not in STREAMS:
        abort(404, message="Stream {} doesn't exist".format(stream_id))

stream_list_parser = reqparse.RequestParser()
stream_list_parser.add_argument('recorder', type=str, help="Recorder to use in stream", required=True)
stream_list_parser.add_argument('market_filter', type=dict, help="Stream market filter, will default to all markets")
stream_list_parser.add_argument(
    'market_data_filter', type=dict, help="Stream market data filter, will default to all data"
)
stream_list_parser.add_argument('description', type=str, help="Stream description")


class StreamList(Resource):

    def get(self):
        return STREAMS

    def post(self):
        args = stream_list_parser.parse_args()
        new_id = create_short_uuid()

        try:
            unique_id = max(i.get('unique_id') for i in STREAMS.values())
        except ValueError:
            unique_id = 0
        unique_id += int(1e3)

        # create new flumine instance
        flumine = Flumine(
            settings=config.SETTINGS,
            recorder=args['recorder'],
            unique_id=unique_id,
        )

        FLUMINES[new_id] = flumine
        STREAMS[new_id] = {
            'status': FLUMINES[new_id].status,
            'running': FLUMINES[new_id].running,
            'description': args['description'],
            'recorder': args['recorder'],
            'market_filter': args['market_filter'],
            'market_data_filter': args['market_data_filter'],
            'unique_id': FLUMINES[new_id].unique_id,
        }
        return STREAMS[new_id], 201


class Stream(Resource):

    def get(self, stream_id):
        abort_if_stream_doesnt_exist(stream_id)
        return STREAMS[stream_id]
