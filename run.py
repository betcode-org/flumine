from api import (
    app,
    api,
)
from api.resources import (
    Settings,
    StreamList,
    Stream,
    RecorderList,
    Recorder
)


api.add_resource(Settings, '/api/settings')
api.add_resource(StreamList, '/api/stream')
api.add_resource(Stream, '/api/stream/<stream_id>')
api.add_resource(RecorderList, '/api/recorder')
api.add_resource(Recorder, '/api/recorder/<recorder_name>')

if __name__ == '__main__':
    app.run(
        debug=True, port=8080
    )
