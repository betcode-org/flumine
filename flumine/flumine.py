import queue
import logging
import threading
from betfairlightweight import (
    APIClient,
    StreamListener,
    BetfairError,
)

from .exceptions import RunError

logger = logging.getLogger('betfairlightweight')
logger.setLevel(logging.INFO)


class Flumine:

    def __init__(self, settings, recorder, unique_id=1e3):
        self.trading = self._create_client(settings)
        self.recorder = recorder
        self.unique_id = unique_id

        self._running = False
        self._socket = None
        self._queue = queue.Queue()
        self._listener = StreamListener(self._queue)

    def start(self):
        """Checks trading is logged in, creates socket,
        subscribes to markets, sets running to True and
        starts handler/run threads.
        """
        logging.info('Starting stream: %s' % self.unique_id)
        if self._running:
            raise RunError('Flumine is already running, call .stop() first')
        self._check_login()
        self._create_socket()
        self.unique_id = self._socket.subscribe_to_markets(
                market_filter=self.recorder.market_filter,
                market_data_filter=self.recorder.market_data_filter,
        )
        self._running = True
        threading.Thread(target=self._run, daemon=True).start()
        threading.Thread(target=self._handler, daemon=False).start()
        return True

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
        return True

    def stream_status(self):
        """Checks sockets status
        """
        return str(self._socket) if self._socket else 'Socket not created'

    @staticmethod
    def _create_client(settings):
        """Returns APIClient based on settings
        """
        return APIClient(
            **settings.get('betfairlightweight')
        )

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
                self.recorder(event)  # todo add error handling to kill

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
                unique_id=self.unique_id,
                description='Flumine Socket',
                listener=self._listener
        )

    @property
    def running(self):
        return True if self._running else False

    @property
    def status(self):
        return 'running' if self._running else 'not running'

    def __str__(self):
        return '<Flumine [%s]>' % self.status

    __repr__ = __str__
