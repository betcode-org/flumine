import queue
import logging
from betfairlightweight import resources

from .strategy.strategy import Strategies, BaseStrategy
from .streams.streams import Streams
from .event import event
from .worker import BackgroundWorker
from .clients.baseclient import BaseClient
from .markets.markets import Markets
from .markets.market import Market

logger = logging.getLogger(__name__)


class BaseFlumine:

    BACKTEST = False

    def __init__(self, client: BaseClient):
        """
        Base framework class

        :param client: flumine client instance
        """
        self.client = client
        self._running = False

        # queues
        self.handler_queue = queue.Queue()

        # all markets
        self.markets = Markets()

        # all strategies
        self.strategies = Strategies()

        # all streams (market/order)
        self.streams = Streams(self)

        # todo order execution class
        self.local_execution = None  # backtesting / paper
        self.betfair_execution = None

        # logging controls (e.g. database logger)
        self._logging_controls = []

        # trading controls
        self._trading_controls = []  # todo register default controls

        # finance blotter
        self.blotter = None  # todo

        # workers
        self._workers = []

    def run(self) -> None:
        raise NotImplementedError

    def add_strategy(self, strategy: BaseStrategy) -> None:
        # create stream if required
        self.streams(strategy)  # create required streams
        self.strategies(strategy)  # store in strategies

    def add_worker(self, worker: BackgroundWorker) -> None:
        self._workers.append(worker)

    def _add_default_workers(self) -> None:
        return

    def _process_market_books(self, event: event.MarketBookEvent) -> None:
        for market_book in event.event:
            market_id = market_book.market_id
            market = self.markets.markets.get(market_id)

            if not market:
                market = self._add_live_market(market_id, market_book)

            for strategy in self.strategies:
                if strategy.check_market(market, market_book):
                    strategy.process_market_book(market, market_book)

    def _add_live_market(
        self, market_id: str, market_book: resources.MarketBook
    ) -> Market:
        live_market = Market(market_id, market_book)
        self.markets.add_market(market_id, live_market)
        # self.blotter.add_market(market_id)
        logger.info(
            "Adding: {0} to live markets and blotter".format(live_market.market_id)
        )
        return live_market

    def _process_raw_data(self, event: event.RawDataEvent) -> None:
        stream_id, publish_time, data = event.event
        for datum in data:
            for strategy in self.strategies:
                if stream_id in strategy.stream_ids:
                    strategy.process_raw_data(publish_time, datum)

    def _process_market_catalogues(self, event: event.MarketCatalogueEvent) -> None:
        for market_catalogue in event.event:
            market = self.markets.markets.get(market_catalogue.market_id)
            if market:
                if market.market_catalogue is None:
                    logger.info(
                        "Updated marketCatalogue for {0}".format(market.market_id)
                    )
                    # todo logging control
                market.market_catalogue = market_catalogue

    def _process_end_flumine(self) -> None:
        for strategy in self.strategies:
            strategy.finish()

    @property
    def status(self) -> str:
        return "running" if self._running else "not running"

    def __enter__(self):
        logger.info("Starting flumine")
        # login
        self.client.login()
        # add default and start all workers
        self._add_default_workers()
        for w in self._workers:
            w.start()
        # todo start logging controls
        # start strategies
        self.strategies.start()
        # start streams
        self.streams.start()

        self._running = True

    def __exit__(self, *args):
        # shutdown streams
        self.streams.stop()
        # todo shutdown thread pools
        # todo shutdown logging controls
        # logout
        self.client.logout()
        self._running = False
        logger.info("Exiting flumine")
