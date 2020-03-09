import queue
import logging
from betfairlightweight import APIClient

from . import utils
from .strategy.strategy import Strategies, BaseStrategy
from .streams.streams import Streams
from .event.event import BaseEvent
from .worker import BackgroundWorker

logger = logging.getLogger(__name__)


class BaseFlumine:
    def __init__(self, trading: APIClient, interactive: bool = False):
        """
        Base framework class

        :param trading: betfairlightweight client instance
        :param interactive: Interactive login for client
        """
        self.trading = trading
        self.interactive = interactive
        self._running = False

        # queues
        self.handler_queue = queue.Queue()

        # all markets
        self.markets = None  # todo

        # all strategies
        self.strategies = Strategies()

        # all streams (market/order)
        self.streams = Streams(self)

        # order execution class
        self.execution = None  # todo

        # logging controls (e.g. database logger)
        self._logging_controls = []

        # trading controls
        self._trading_controls = []
        # todo register default controls

        # finance blotter
        self.blotter = None  # todo

        # workers
        self._workers = [
            BackgroundWorker(
                interval=1200,
                function=utils.keep_alive,
                args=(self.trading, self.interactive),
            )
        ]

    def run(self) -> None:
        raise NotImplementedError

    def add_strategy(self, strategy: BaseStrategy) -> None:
        # create stream if required
        self.streams(strategy)  # create required streams
        self.strategies(strategy)  # store in strategies

    def add_worker(self, worker: BackgroundWorker) -> None:
        self._workers.append(worker)

    def _process_market_books(self, event: BaseEvent) -> None:
        for market_book in event.event:
            for strategy in self.strategies:
                if strategy.check_market(market_book):
                    strategy.process_market_book(market_book)

    def _process_raw_data(self, event: BaseEvent) -> None:
        stream_id, publish_time, data = event.event
        for datum in data:
            for strategy in self.strategies:
                if stream_id in strategy.stream_ids:
                    strategy.process_raw_data(publish_time, datum)

    def _process_end_flumine(self) -> None:
        for strategy in self.strategies:
            strategy.finish()

    @property
    def status(self) -> str:
        return "running" if self._running else "not running"

    def __enter__(self):
        logger.info("Starting flumine")
        # login
        if self.interactive:
            self.trading.login_interactive()
        else:
            self.trading.login()
        # start workers
        for w in self._workers:
            w.start()
        # start strategies
        self.strategies.start()
        # start streams
        self.streams.start()

        self._running = True

    def __exit__(self, *args):
        # shutdown streams
        self.streams.stop()
        # shutdown thread pools
        # todo
        # shutdown logging controls
        # todo
        # logout
        self.trading.logout()
        self._running = False
        logger.info("Exiting flumine")
