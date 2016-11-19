import queue
import threading
from betfairlightweight import StreamListener, BetfairError

from .exceptions import RunError


class Flumine:

    def __init__(self, trading, recorder):
        self.trading = trading
        self.recorder = recorder

        self._running = False
        self._socket = None
        self._queue = queue.Queue()
        self._listener = StreamListener(self._queue)

        self._handler_thread = threading.Thread(target=self._handler, daemon=True)
        self._handler_thread.start()

    def start(self):
        """Checks trading is logged in, creates socket,
        subscribes to markets, sets running to True and
        starts handler/run threads.
        """
        if self._running:
            raise RunError()
        self._check_login()
        self._create_socket()
        self._socket.subscribe_to_markets(
                unique_id=2,
                market_filter=self.recorder.market_filter,
                market_data_filter=self.recorder.market_data_filter,
        )
        self._running = True
        threading.Thread(target=self._run, daemon=True).start()

    def stop(self):
        """Stops socket, sets running to false
        and socket to None
        """
        if self._socket:
            self._socket.stop()
        self._running = False
        self._socket = None

    def _handler(self):
        """Handles output from queue which
        is filled by the listener.
        """
        while self._running:
            events = self._queue.get()
            for event in events:
                self.recorder(event)

    def _run(self):
        """ Runs socket and catches any errors
        """
        try:
            self._socket.start(async=False)
        except BetfairError as e:
            self.stop()
            print('flumine error', e)

    def _check_login(self):
        """Login if session expired
        """
        if self.trading.session_expired:
            self.trading.login()

    def _create_socket(self):
        """Creates stream
        """
        self._socket = self.trading.streaming.create_stream(
                unique_id=1,
                description='Flumine Socket',
                listener=self._listener
        )

    def stream_status(self):
        """Checks sockets status
        """
        return str(self._socket) if self._socket else 'Socket not created'

    def __repr__(self):
        return str(self)

    def __str__(self):
        return '<Flumine [%s]>' % ('running' if self._running else 'not running')
