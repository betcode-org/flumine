import queue
import logging
from betfairlightweight import APIClient

from .strategy.strategy import Strategies
from .streams.streams import Streams

logger = logging.getLogger(__name__)


class BaseFlumine:
    def __init__(self, trading: APIClient):
        self.trading = trading
        self._running = False

        # queues
        self.handler_queue = queue.Queue()
        self.background_queue = queue.Queue()

        # all markets
        self.markets = None  # todo

        # all strategies
        self.strategies = Strategies()

        # all streams (market/order)
        self.streams = Streams()

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

    def add_strategy(self, strategy):
        # create stream if required
        self.streams(strategy)  # create required streams
        self.strategies(strategy)  # store in strategies

    @property
    def status(self) -> str:
        return "running" if self._running else "not running"

    def __enter__(self):
        # start streams
        self.streams.start()

        self.trading.login()
        self._running = True

    def __exit__(self, *args):
        # shutdown streams
        self.streams.stop()

        # shutdown thread pools
        # todo

        # shutdown logging controls
        # todo

        self.trading.logout()
        self._running = False
