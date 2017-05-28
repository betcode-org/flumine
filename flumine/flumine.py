import queue
import logging
import threading
from betfairlightweight import APIClient, StreamListener, BetfairError

from .exceptions import RunError


class Flumine:

    def __init__(self, trading, recorder):
        self.trading = self._create_client(trading)
        self.recorder = recorder

        self._running = False
        self._socket = None
        self._queue = queue.Queue()
        self._listener = StreamListener(self._queue)

    def start(self):
        """Checks trading is logged in, creates socket,
        subscribes to markets, sets running to True and
        starts handler/run threads.
        """
        if self._running:
            raise RunError('Flumine is already running, call .stop() first')
        self._check_login()
        self._create_socket()
        self._socket.subscribe_to_markets(
                market_filter=self.recorder.market_filter,
                market_data_filter=self.recorder.market_data_filter,
        )
        self._running = True
        threading.Thread(target=self._run, daemon=True).start()
        threading.Thread(target=self._handler, daemon=False).start()

    def stop(self):
        """Stops socket, sets running to false
        and socket to None
        """
        if not self._running:
            raise RunError('Flumine is not running')
        if self._socket:
            self._socket.stop()
        self._running = False
        self._socket = None

    def stream_status(self):
        """Checks sockets status
        """
        return str(self._socket) if self._socket else 'Socket not created'

    @staticmethod
    def _create_client(trading):
        """Returns APIClient if tuple provided
        """
        if isinstance(trading, tuple):
            return APIClient(username=trading[0])
        else:
            return trading

    def _handler(self):
        """Handles output from queue which
        is filled by the listener.
        """
        while self._running:
            try:
                events = self._queue.get(timeout=0.01)
            except queue.Empty:
                continue
            for event in events:
                self.recorder(event)

    def _run(self):
        """ Runs socket and catches any errors
        """
        try:
            self._socket.start(async=False)
        except BetfairError as e:
            logging.info('Betfair error: %s' % e)
            self.stop()

    def _check_login(self):
        """Login if session expired
        """
        if self.trading.session_expired:
            self.trading.login()

    def _create_socket(self):
        """Creates stream
        """
        self._socket = self.trading.streaming.create_stream(
                unique_id=1000,
                description='Flumine Socket',
                listener=self._listener
        )

    def __str__(self):
        return '<Flumine [%s]>' % ('running' if self._running else 'not running')

    __repr__ = __str__
