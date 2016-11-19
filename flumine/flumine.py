import queue
import threading
from betfairlightweight import StreamListener


class Flumine:

    def __init__(self, trading, recorder):
        self.trading = trading
        self.recorder = recorder

        self._running = False
        self._socket = None
        self._queue = queue.Queue()
        self._listener = StreamListener(self._queue)

    def handler(self):
        while self._running:
            events = self._queue.get()
            for event in events:
                self.recorder(event)
        print('end handler')

    def start(self):
        self._check_login()
        self._create_socket()
        self._socket.subscribe_to_markets(
                unique_id=2,
                market_filter=self.recorder.market_filter,
                market_data_filter=self.recorder.market_data_filter,
        )
        self._running = True
        threading.Thread(target=self.handler, daemon=True).start()
        self._socket.start(async=True)

    def stop(self):
        self._socket.stop()
        self._running = False

    def _check_login(self):
        if self.trading.session_expired:
            self.trading.login()

    def _create_socket(self):
        self._socket = self.trading.streaming.create_stream(
                unique_id=1,
                description='Flumine Socket',
                listener=self._listener
        )

    def stream_status(self):
        return str(self._socket)

    def __str__(self):
        return '<Flumine [%s]>' % ('running' if self._running else 'not running')
