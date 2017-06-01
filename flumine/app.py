import json
from flask import (
    Flask,
    request,
    jsonify
)
import inspect

from .resources import recorder
from .storage import storageengine
from .utils import create_short_uuid
from . import (
    Flumine,
    FlumineException,
)


# load settings
with open('flumine_settings.json') as data_file:
    SETTINGS = json.load(data_file)

# storage engine
engine_settings = SETTINGS['storage']
ENGINES = {
    obj.NAME: {'name': name, 'obj': obj} for name, obj in inspect.getmembers(storageengine) if inspect.isclass(obj)
}
storage_engine = ENGINES[engine_settings['engine']]['obj'](engine_settings['directory'])

# recorder data
RECORDERS = {
    obj.NAME: {'name': name, 'obj': obj} for name, obj in inspect.getmembers(recorder) if inspect.isclass(obj)
}

# stream data
STREAMS = {}


# flask stuff
app = Flask(__name__)


def create_stream_info(stream_id):
    stream = STREAMS[stream_id]
    flumine = stream['flumine']
    return {
        'unique_id': flumine.unique_id,
        'running': flumine.running,
        'description': stream['description'],
        'recorder': stream['recorder'],
        'market_filter': stream['market_filter'],
        'market_data_filter': stream['market_data_filter'],
        # 'uri': url_for('stream.get', stream_id=stream_id),
    }


@app.route("/")
def hello():
    return "Hello World!"


@app.route("/api/settings")
def settings():
    return jsonify(SETTINGS)


@app.route("/api/recorder")
def recorders():
    return jsonify(
        {obj.NAME: {'name': name} for name, obj in inspect.getmembers(recorder) if inspect.isclass(obj)}
    )

@app.route("/api/storage")
def storage():
    return jsonify(storage_engine.extra)


@app.route("/api/stream")
def streams():
    return jsonify(
        {stream_id: create_stream_info(stream_id) for stream_id in STREAMS}
    )


@app.route("/api/stream", methods=['POST'])
def post_stream():
    args = request.json or request.form.to_dict()
    stream_recorder = RECORDERS[args['recorder']]
    new_id = create_short_uuid()

    try:
        unique_id = max(i.get('unique_id') for i in STREAMS.values())
    except ValueError:
        unique_id = 0
    unique_id += int(1e3)

    # create new flumine instance
    flumine = Flumine(
        settings=SETTINGS,
        recorder=stream_recorder['obj'](
            storage_engine=storage_engine,
            market_filter=args.get('market_filter'),
            market_data_filter=args.get('market_data_filter'),
        ),
        unique_id=unique_id,
    )

    STREAMS[new_id] = {
        'flumine': flumine,
        'description': args.get('description'),
        'recorder': args['recorder'],
        'market_filter': args.get('market_filter'),
        'market_data_filter': args.get('market_data_filter'),
        'unique_id': unique_id,
    }
    return jsonify(create_stream_info(new_id))


@app.route("/api/stream/<stream_id>")
def get_stream(stream_id):
    stream = STREAMS[stream_id]
    flumine = stream['flumine']
    return jsonify({
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
            'time_created': flumine._listener.stream.time_created.strftime(
                '%Y-%m-%dT%H:%M:%S.%fZ') if flumine._listener.stream else None,
            'time_updated': flumine._listener.stream.time_updated.strftime(
                '%Y-%m-%dT%H:%M:%S.%fZ') if flumine._listener.stream else None,
        },
    })


@app.route("/api/stream/<stream_id>/start")
def stream_start(stream_id):
    streaming_settings = SETTINGS['streaming']
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
    return jsonify({
        'success': response,
        'error': error,
        'error_code': error_code,
    })


@app.route("/api/stream/<stream_id>/stop")
def stream_stop(stream_id):
    try:
        response = STREAMS[stream_id]['flumine'].stop()
        error, error_code = None, None
    except FlumineException as e:
        response = False
        error = str(e)
        error_code = e.__class__.__name__
    return jsonify({
        'success': response,
        'error': error,
        'error_code': error_code,
    })
