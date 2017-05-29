import json
from flask_restful import (
    Resource,
    abort,
    reqparse,
    output_json,
)
from flask import url_for, request

from .. import app
from ..utils import create_short_uuid
from .. import config
from flumine import (
    Flumine,
    FlumineException,
)
from .recorder import RECORDERS


# stream data
STREAMS = {}

HEADERS = {
    'content-type': 'application/json'
}

# load settings
with open('flumine_settings.json') as data_file:
    config.SETTINGS = json.load(data_file)


def abort_if_stream_doesnt_exist(stream_id):
    if stream_id not in STREAMS:
        abort(404, message="Stream {} doesn't exist".format(stream_id))


def abort_if_recorder_doesnt_exist(recorder_name):
    if recorder_name not in RECORDERS:
        abort(404, message="Recorder {} doesn't exist".format(recorder_name))
    else:
        return RECORDERS[recorder_name]

stream_list_parser = reqparse.RequestParser()
stream_list_parser.add_argument('recorder', type=str, help="Recorder to use in stream", required=True)
stream_list_parser.add_argument('description', type=str, help="Stream description")
stream_list_parser.add_argument('market_filter', type=dict, help="Stream market filter, will default to all markets")
stream_list_parser.add_argument(
    'market_data_filter', type=dict, help="Stream market data filter, will default to all data"
)


def create_stream_info(stream_id):
    stream = STREAMS[stream_id]
    flumine = stream['flumine']
    return {
        'status': flumine.status,
        'running': flumine.running,
        'description': stream['description'],
        'recorder': stream['recorder'],
        'market_filter': stream['market_filter'],
        'market_data_filter': stream['market_data_filter'],
        'unique_id': flumine.unique_id,
        # 'uri': url_for('stream.get', stream_id=stream_id),
    }


class StreamList(Resource):

    def get(self):
        return {
            stream_id: create_stream_info(stream_id) for stream_id in STREAMS
        }

    def post(self):
        args = stream_list_parser.parse_args()
        # verify recorder
        recorder = abort_if_recorder_doesnt_exist(
            args['recorder']
        )
        new_id = create_short_uuid()

        try:
            unique_id = max(i.get('unique_id') for i in STREAMS.values())
        except ValueError:
            unique_id = 0
        unique_id += int(1e3)

        # create new flumine instance
        flumine = Flumine(
            settings=config.SETTINGS,
            recorder=recorder['obj'](
                market_filter=args['market_filter'],
                market_data_filter=args['market_data_filter'],
            ),
            unique_id=unique_id,
        )

        STREAMS[new_id] = {
            'flumine': flumine,
            'description': args['description'],
            'recorder': args['recorder'],
            'market_filter': args['market_filter'],
            'market_data_filter': args['market_data_filter'],
            'unique_id': unique_id,
        }
        return create_stream_info(new_id), 201


stream_start_parser = reqparse.RequestParser()
stream_start_parser.add_argument('conflate_msg', type=int, help="Conflation ms to be used")
stream_start_parser.add_argument('heartbeat_ms', type=int, help="Heartbeat ms to be used")
stream_start_parser.add_argument('segmentation_enabled', type=bool, help="Segmentation enabled or not")


class Stream(Resource):

    def get(self, stream_id):
        abort_if_stream_doesnt_exist(stream_id)
        stream = STREAMS[stream_id]
        flumine = stream['flumine']

        return {
            'status': flumine.status,
            'running': flumine.running,
            'description': stream['description'],
            'recorder': stream['recorder'],
            'market_filter': stream['market_filter'],
            'market_data_filter': stream['market_data_filter'],
            'unique_id': flumine.unique_id,
            'listener': {
                'stream_type': flumine._listener.stream_type,
                'market_count': len(flumine._listener.stream._caches) if flumine._listener.stream else None,
                'updates_processed': flumine._listener.stream._updates_processed if flumine._listener.stream else None,
                'time_created': flumine._listener.stream.time_created.strftime('%Y-%m-%dT%H:%M:%S.%fZ') if flumine._listener.stream else None,
                'time_updated': flumine._listener.stream.time_updated.strftime('%Y-%m-%dT%H:%M:%S.%fZ') if flumine._listener.stream else None,
            },
            'start': url_for('start', stream_id=stream_id),
            'stop': url_for('stop', stream_id=stream_id),
        }, 200

    @staticmethod
    @app.route('/api/stream/<stream_id>/start', methods=['get'])
    def start(stream_id):
        abort_if_stream_doesnt_exist(stream_id)
        streaming_settings = config.SETTINGS['streaming']
        try:
            response = STREAMS[stream_id]['flumine'].start(
                heartbeat_ms=request.args.get('heartbeat_ms', streaming_settings['heartbeat_ms']),
                conflate_ms=request.args.get('conflate_ms', streaming_settings['conflate_ms']),
                segmentation_enabled=request.args.get('segmentation_enabled', streaming_settings['segmentation_enabled'])
            )
            error, error_code = None, None
        except FlumineException as e:
            response = False
            error = str(e)
            error_code = e.__class__.__name__
        return output_json({
            'success': response,
            'error': error,
            'error_code': error_code,
        }, 200, headers=HEADERS)

    @staticmethod
    @app.route('/api/stream/<stream_id>/stop', methods=['get'])
    def stop(stream_id):
        abort_if_stream_doesnt_exist(stream_id)
        try:
            response = STREAMS[stream_id]['flumine'].stop()
            error, error_code = None, None
        except FlumineException as e:
            response = False
            error = str(e)
            error_code = e.__class__.__name__
        return output_json({
            'success': response,
            'error': error,
            'error_code': error_code,
        }, 200, headers=HEADERS)
