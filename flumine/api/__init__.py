from flask import Flask
from flask_restful import (
    Api,
)

from .resources import (
    Settings,
    StreamList,
    Stream,
    StreamStart,
    StreamStop,
    RecorderList,
    Recorder
)

app = Flask(__name__)
api = Api(app)

api.add_resource(Settings, '/api/settings')
api.add_resource(StreamList, '/api/stream')
api.add_resource(Stream, '/api/stream/<stream_id>')
api.add_resource(StreamStart, '/api/stream/<stream_id>/start')
api.add_resource(StreamStop, '/api/stream/<stream_id>/stop')
api.add_resource(RecorderList, '/api/recorder')
api.add_resource(Recorder, '/api/recorder/<recorder_name>')
