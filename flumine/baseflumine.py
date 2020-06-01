import queue
import logging
from typing import Type
from betfairlightweight import resources

from .strategy.strategy import Strategies, BaseStrategy
from .streams.streams import Streams
from .events import events
from .worker import BackgroundWorker
from .clients.baseclient import BaseClient
from .markets.markets import Markets
from .markets.market import Market
from .markets.middleware import Middleware
from .execution.betfairexecution import BetfairExecution
from .execution.simulatedexecution import SimulatedExecution
from .order.process import process_current_orders
from .controls.clientcontrols import BaseControl, MaxOrderCount
from .controls.tradingcontrols import OrderValidation, StrategyExposure
from .controls.loggingcontrols import LoggingControl
from . import config, utils


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
        self.cleared_market_queue = queue.Queue()

        # all markets
        self.markets = Markets()
        self._market_middleware = []

        # all strategies
        self.strategies = Strategies()

        # all streams (market/order)
        self.streams = Streams(self)
        self.streams.add_client(client)

        # order execution class
        self.simulated_execution = SimulatedExecution(self)
        self.betfair_execution = BetfairExecution(self)

        # logging controls (e.g. database logger)
        self._logging_controls = []

        # trading controls
        self._trading_controls = []
        # add default controls (processed in order)
        self.add_trading_control(OrderValidation)
        self.add_trading_control(StrategyExposure)
        # register default client controls (processed in order)
        self.add_client_control(MaxOrderCount)

        # workers
        self._workers = []

    def run(self) -> None:
        raise NotImplementedError

    def add_strategy(self, strategy: BaseStrategy) -> None:
        self.streams(strategy)  # create required streams
        self.strategies(strategy)  # store in strategies
        self.log_control(events.StrategyEvent(strategy))

    def add_worker(self, worker: BackgroundWorker) -> None:
        self._workers.append(worker)

    def add_client_control(self, client_control: Type[BaseControl], **kwargs) -> None:
        logger.info("Adding client control {0}".format(client_control.NAME))
        self.client.trading_controls.append(client_control(self, self.client, **kwargs))

    def add_trading_control(self, trading_control: Type[BaseControl], **kwargs) -> None:
        logger.info("Adding trading control {0}".format(trading_control.NAME))
        self._trading_controls.append(trading_control(self, **kwargs))

    def add_market_middleware(self, middleware: Middleware) -> None:
        logger.info("Adding market middleware {0}".format(middleware))
        self._market_middleware.append(middleware)

    def add_logging_control(self, logging_control: LoggingControl) -> None:
        logger.info("Adding logging control {0}".format(logging_control.NAME))
        self._logging_controls.append(logging_control)

    def log_control(self, event: events.BaseEvent) -> None:
        for logging_control in self._logging_controls:
            logging_control.logging_queue.put(event)

    def _add_default_workers(self) -> None:
        return

    def _process_market_books(self, event: events.MarketBookEvent) -> None:
        for market_book in event.event:
            market_id = market_book.market_id
            if market_book.status == "CLOSED":
                self.handler_queue.put(events.CloseMarketEvent(market_book))
                continue

            market = self.markets.markets.get(market_id)
            if market is None:
                market = self._add_live_market(market_id, market_book)

            # process market
            market(market_book)

            # process middleware
            for middleware in self._market_middleware:
                middleware(market)  # todo err handling?

            for strategy in self.strategies:
                if utils.call_check_market(strategy.check_market, market, market_book):
                    utils.call_process_market_book(
                        strategy.process_market_book, market, market_book
                    )

            self._process_market_orders(market)

    def _process_market_orders(self, market: Market) -> None:
        for order_package in market.blotter.process_orders(self.client):
            self.handler_queue.put(order_package)

    def _process_order_package(self, order_package) -> None:
        """Validate trading controls and
        then execute.
        """
        for control in self._trading_controls:
            control(order_package)
        for control in order_package.client.trading_controls:
            control(order_package)
        if order_package.orders:
            order_package.client.execution.handler(order_package)
        else:
            logger.warning("Empty package, not executing", extra=order_package.info)

    def _add_live_market(
        self, market_id: str, market_book: resources.MarketBook
    ) -> Market:
        market = Market(self, market_id, market_book)
        self.markets.add_market(market_id, market)
        logger.info("Adding: {0} to markets".format(market.market_id))
        return market

    def _process_raw_data(self, event: events.RawDataEvent) -> None:
        stream_id, publish_time, data = event.event
        for datum in data:
            for strategy in self.strategies:
                if stream_id in strategy.stream_ids:
                    strategy.process_raw_data(publish_time, datum)

    def _process_market_catalogues(self, event: events.MarketCatalogueEvent) -> None:
        for market_catalogue in event.event:
            market = self.markets.markets.get(market_catalogue.market_id)
            if market:
                if market.market_catalogue is None:
                    market.market_catalogue = market_catalogue
                    self.log_control(events.MarketEvent(market))
                    logger.info(
                        "Updated marketCatalogue for {0}".format(market.market_id)
                    )
                else:
                    market.market_catalogue = market_catalogue

    def _process_current_orders(self, event: events.CurrentOrdersEvent) -> None:
        process_current_orders(self.markets, self.strategies, event)  # update state
        for market in self.markets:
            if market.closed is False:
                for strategy in self.strategies:
                    strategy_orders = market.blotter.strategy_orders(strategy)
                    strategy.process_orders(market, strategy_orders)
            self._process_market_orders(market)

    def _process_custom_event(self, event: events.CustomEvent) -> None:
        try:
            event.callback(self, event)
        except Exception as e:
            logger.exception(
                "Unknown error {0} in _process_custom_event {1}".format(
                    e, event.callback
                )
            )
        for market in self.markets:
            self._process_market_orders(market)

    def _process_close_market(self, event: events.CloseMarketEvent) -> None:
        market_id = event.event.market_id
        market = self.markets.markets.get(market_id)
        if market is None:
            logger.warning(
                "Market %s not present when closing" % market_id,
                extra={"market_id": market_id},
            )
            return
        market.close_market()
        market.blotter.process_closed_market(event.event)

        for strategy in self.strategies:
            if market.market_book.streaming_unique_id in strategy.stream_ids:
                strategy.process_closed_market(market, event.event)

        self.cleared_market_queue.put(market.market_id)
        self.log_control(event)

    def _process_cleared_orders(self, event):
        # todo update blotter?
        logger.info(
            "Market closed and cleared", extra={"market_id": event.event.market_id},
        )

    def _process_cleared_markets(self, event: events.ClearedMarketsEvent):
        # todo update blotter?
        for cleared_market in event.event.orders:
            logger.info(
                "Market level cleared",
                extra={
                    "market_id": cleared_market.market_id,
                    "profit": cleared_market.profit,
                    "bet_count": cleared_market.bet_count,
                },
            )

    def _process_end_flumine(self) -> None:
        for strategy in self.strategies:
            strategy.finish()

    def __enter__(self):
        logger.info("Starting flumine")
        # add execution to clients
        self.client.add_execution(self)
        # simulated
        if self.BACKTEST:
            config.simulated = True
        else:
            config.simulated = False
        # login
        self.client.login()
        self.client.update_account_details()
        # add default and start all workers
        self._add_default_workers()
        for w in self._workers:
            w.start()
        # start logging controls
        for c in self._logging_controls:
            c.start()
        # start strategies
        self.strategies.start()
        # start streams
        self.streams.start()

        self._running = True

    def __exit__(self, *args):
        # shutdown streams
        self.streams.stop()
        # shutdown thread pools
        self.simulated_execution.shutdown()
        self.betfair_execution.shutdown()
        # shutdown logging controls
        self.log_control(events.TerminationEvent(None))
        for c in self._logging_controls:
            if c.is_alive():
                c.join()
        # logout
        self.client.logout()
        self._running = False
        logger.info("Exiting flumine")
