import queue
import logging
from betfairlightweight import APIClient

logger = logging.getLogger(__name__)


class BaseFlumine:
    def __init__(self, trading: APIClient):
        self.trading = trading
        self._running = False

        # queues
        self.handler_queue = queue.Queue()
        self.background_queue = queue.Queue()

        # all streams (market/order)
        self.streams = None  # todo

        # order execution class
        self.execution = None  # todo

        # logging controls (e.g. database logger)
        self._logging_controls = []

        # trading controls
        self._trading_controls = []
        # todo register default controls

        # finance blotter
        self.blotter = None  # todo

    def run(self) -> None:
        raise NotImplementedError

    @property
    def status(self) -> str:
        return "running" if self._running else "not running"

    def __enter__(self):
        self.trading.login()
        self._running = True

    def __exit__(self, *args):
        # shutdown streams

        # shutdown thread pools

        # shutdown logging controls

        self.trading.logout()
        self._running = False
