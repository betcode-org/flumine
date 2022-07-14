import time
import queue
import logging
import threading
from typing import Type
from betfairlightweight import resources

from .strategy.strategy import Strategies, BaseStrategy
from .streams.streams import Streams
from .events import events
from .worker import BackgroundWorker
from .clients import Clients, BaseClient
from .markets.markets import Markets
from .markets.market import Market
from .markets.middleware import Middleware, SimulatedMiddleware
from .execution.betfairexecution import BetfairExecution
from .execution.simulatedexecution import SimulatedExecution
from .order.process import process_current_orders
from .controls.clientcontrols import BaseControl, MaxTransactionCount
from .controls.tradingcontrols import (
    OrderValidation,
    StrategyExposure,
    MarketValidation,
)
from .controls.loggingcontrols import LoggingControl
from .exceptions import FlumineException, ClientError
from . import config, utils

logger = logging.getLogger(__name__)


class BaseFlumine:

    SIMULATED = False

    def __init__(self, client: BaseClient = None):
        """
        Base framework class

        :param client: flumine client instance
        """
        self._running = False
        # streams (market/order)
        self.streams = Streams(self)

        self.clients = Clients()

        # FIFO queue
        self.handler_queue = queue.Queue()

        # markets
        self.markets = Markets()

        # middleware
        self._market_middleware = []

        # strategies
        self.strategies = Strategies()

        # order execution class
        self.simulated_execution = SimulatedExecution(
            self, config.max_execution_workers
        )
        self.betfair_execution = BetfairExecution(self, config.max_execution_workers)

        # add client
        if client:
            self.add_client(client)

        # logging controls (e.g. database logger)
        self._logging_controls = []

        # trading controls
        self.trading_controls = []
        # add default controls (processed in order)
        self.add_trading_control(OrderValidation)
        self.add_trading_control(MarketValidation)
        self.add_trading_control(StrategyExposure)

        # workers
        self._workers = []

    def run(self) -> None:
        raise NotImplementedError

    def add_client(self, client: BaseClient) -> None:
        self.clients.add_client(client)
        self.streams.add_client(client)
        # add execution
        client.add_execution(self)
        # add simulation middleware if required
        if self.clients.simulated and not any(
            isinstance(val, SimulatedMiddleware) for val in self._market_middleware
        ):
            self.add_market_middleware(SimulatedMiddleware())
        # register default client controls (processed in order)
        self.add_client_control(client, MaxTransactionCount)

    def add_strategy(self, strategy: BaseStrategy) -> None:
        logger.info("Adding strategy {0}".format(strategy))
        self.streams(strategy)  # create required streams
        self.strategies(strategy, self.clients)  # store in strategies
        self.log_control(events.StrategyEvent(strategy))

    def add_worker(self, worker: BackgroundWorker) -> None:
        logger.info("Adding worker {0}".format(worker.name))
        self._workers.append(worker)

    def add_client_control(
        self, client: BaseClient, client_control: Type[BaseControl], **kwargs
    ) -> None:
        logger.info("Adding client control {0}".format(client_control.NAME))
        client.trading_controls.append(client_control(self, client, **kwargs))

    def add_trading_control(self, trading_control: Type[BaseControl], **kwargs) -> None:
        logger.info("Adding trading control {0}".format(trading_control.NAME))
        self.trading_controls.append(trading_control(self, **kwargs))

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

            # check latency (only if marketBook is from a stream update)
            if market_book.streaming_snap is False:
                latency = time.time() - (market_book.publish_time_epoch / 1e3)
                if latency > 2:
                    logger.warning(
                        "High latency between current time and MarketBook publish time",
                        extra={
                            "market_id": market_id,
                            "latency": latency,
                            "pt": market_book.publish_time,
                        },
                    )

            market = self.markets.markets.get(market_id)
            if market is None:
                market = self._add_market(market_id, market_book)
            elif market.closed:
                self.markets.add_market(market_id, market)

            if market_book.status == "CLOSED":
                self.handler_queue.put(events.CloseMarketEvent(market_book))
                continue

            # process market
            market(market_book)

            # process middleware
            for middleware in self._market_middleware:
                utils.call_middleware_error_handling(middleware, market)

            for strategy in self.strategies:
                if utils.call_strategy_error_handling(
                    strategy.check_market, market, market_book
                ):
                    utils.call_strategy_error_handling(
                        strategy.process_market_book, market, market_book
                    )

    def _process_sports_data(self, event: events.SportsDataEvent) -> None:
        for sports_data in event.event:
            # get marketId
            market_id = sports_data.market_id
            # get market
            market = self.markets.markets.get(market_id)
            if market is None:
                logger.error(
                    "Market not present for sports data", extra={"market_id": market_id}
                )
                continue
            for strategy in self.strategies:
                if sports_data.streaming_unique_id in strategy.stream_ids:
                    utils.call_strategy_error_handling(
                        strategy.process_sports_data, market, sports_data
                    )

    def process_order_package(self, order_package) -> None:
        """Execute through client."""
        order_package.client.execution.handler(order_package)

    def _add_market(self, market_id: str, market_book: resources.MarketBook) -> Market:
        logger.info("Adding: {0} to markets".format(market_id))
        market = Market(self, market_id, market_book)
        self.markets.add_market(market_id, market)
        for middleware in self._market_middleware:
            middleware.add_market(market)
        return market

    def _remove_market(self, market: Market, clear: bool = True) -> None:
        logger.info("Removing market {0}".format(market.market_id), extra=self.info)
        for middleware in self._market_middleware:
            middleware.remove_market(market)
        for strategy in self.strategies:
            strategy.remove_market(market.market_id)
        if clear:
            self.markets.remove_market(market.market_id)

    def _process_raw_data(self, event: events.RawDataEvent) -> None:
        stream_id, clk, publish_time, data = event.event
        for datum in data:
            if "id" in datum:
                market_id = datum["id"]
                market = self.markets.markets.get(market_id)
                if market is None:
                    self._add_market(market_id, None)
                elif market.closed:
                    self.markets.add_market(market_id, market)

                if (
                    "marketDefinition" in datum
                    and datum["marketDefinition"]["status"] == "CLOSED"
                ):
                    datum["_stream_id"] = stream_id
                    self.handler_queue.put(events.CloseMarketEvent(datum))

            for strategy in self.strategies:
                if stream_id in strategy.stream_ids:
                    strategy.process_raw_data(clk, publish_time, datum)

    def _process_market_catalogues(self, event: events.MarketCatalogueEvent) -> None:
        for market_catalogue in event.event:
            market = self.markets.markets.get(market_catalogue.market_id)
            if market:
                if market.market_catalogue is None:
                    market.market_catalogue = market_catalogue
                    self.log_control(events.MarketEvent(market))
                    logger.info(
                        "Created marketCatalogue for {0}".format(market.market_id),
                        extra=market.info,
                    )
                else:
                    market.market_catalogue = market_catalogue
                    logger.info(
                        "Updated marketCatalogue for {0}".format(market.market_id),
                        extra=market.info,
                    )
                market.update_market_catalogue = False

    def _process_current_orders(self, event: events.CurrentOrdersEvent) -> None:
        # update state
        if event.event:
            process_current_orders(
                self.markets, self.strategies, event, self.log_control, self._add_market
            )
        for market in self.markets:
            if market.closed is False and market.blotter.active:
                for strategy in self.strategies:
                    strategy_orders = market.blotter.strategy_orders(strategy)
                    if strategy_orders:
                        utils.call_process_orders_error_handling(
                            strategy, market, strategy_orders
                        )

    def _process_custom_event(self, event: events.CustomEvent) -> None:
        try:
            event.callback(self, event)
        except FlumineException as e:
            logger.error(
                "FlumineException error {0} in _process_custom_event {1}".format(
                    e, event.callback
                ),
                exc_info=True,
            )
        except Exception as e:
            logger.exception(
                "Unknown error {0} in _process_custom_event {1}".format(
                    e, event.callback
                ),
                exc_info=True,
            )
            if config.raise_errors:
                raise

    def _process_close_market(self, event: events.CloseMarketEvent) -> None:
        market_book = event.event
        if isinstance(market_book, dict):
            recorder = True
            market_id = market_book["id"]
            stream_id = market_book["_stream_id"]
        else:
            recorder = False
            market_id = market_book.market_id
            stream_id = market_book.streaming_unique_id
        market = self.markets.markets.get(market_id)
        if market is None:
            logger.warning(
                "Market %s not present when closing" % market_id,
                extra={"market_id": market_id, **self.info},
            )
            return
        # process market
        if market.closed is False:
            market.close_market()
        if recorder is False:
            market(market_book)
            market.blotter.process_closed_market(event.event)

        for strategy in self.strategies:
            if stream_id in strategy.stream_ids:
                strategy.process_closed_market(market, event.event)

        if recorder is False and self.clients.simulated:
            # simulate ClearedOrdersEvent
            cleared_orders = resources.ClearedOrders(
                moreAvailable=False, clearedOrders=[]
            )
            cleared_orders.market_id = market_id
            self._process_cleared_orders(events.ClearedOrdersEvent(cleared_orders))
            for client in self.clients:
                # simulate ClearedMarketsEvent
                cleared_markets = resources.ClearedOrders(
                    moreAvailable=False,
                    clearedOrders=[market.cleared(client)],
                )
                self._process_cleared_markets(
                    events.ClearedMarketsEvent(cleared_markets)
                )
        self.log_control(event)
        logger.info("Market closed", extra={"market_id": market_id, **self.info})

        # check for markets that have been closed for x seconds and remove
        if not self.clients.simulated:
            # due to monkey patching this will clear simulated markets
            closed_markets = [
                m
                for m in self.markets
                if m.closed
                and m.elapsed_seconds_closed
                and m.elapsed_seconds_closed > 3600
            ]
            for market in closed_markets:
                self._remove_market(market)
        else:
            self._remove_market(market, clear=False)

    def _process_cleared_orders(self, event):
        market_id = event.event.market_id
        market = self.markets.markets.get(market_id)
        if market is None:
            logger.warning(
                "Market %s not present when clearing" % market_id,
                extra={"market_id": market_id, **self.info},
            )
            return

        meta_orders = market.blotter.process_cleared_orders(event.event)
        self.log_control(events.ClearedOrdersMetaEvent(meta_orders))
        logger.info(
            "Market cleared",
            extra={
                "market_id": market_id,
                "order_count": len(meta_orders),
                **self.info,
            },
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
        self.log_control(event)

    def _process_end_flumine(self) -> None:
        self.strategies.finish(self)

    @property
    def info(self) -> dict:
        return {
            "clients": self.clients.info,
            "markets": {
                "market_count": len(self.markets),
                "open_market_count": len(self.markets.open_market_ids),
            },
            "streams": [s for s in self.streams],
            "logging_controls": self._logging_controls,
            "threads": threading.enumerate(),
        }

    def __enter__(self):
        logger.info("Starting flumine", extra=self.info)
        if len(self.clients) == 0:
            raise ClientError("No clients provided")
        # simulated
        if self.SIMULATED:
            config.simulated = True
        else:
            config.simulated = False
        # login
        self.clients.login()
        self.clients.update_account_details()
        # add default and start all workers
        self._add_default_workers()
        for w in self._workers:
            w.start()
        # start logging controls
        for c in self._logging_controls:
            c.start()
        # process config (logging)
        self.log_control(events.ConfigEvent(config))
        # start strategies
        self.strategies.start()
        # start streams
        self.streams.start()

        self._running = True

    def __exit__(self, *args):
        # shutdown framework
        self._process_end_flumine()
        # shutdown workers
        for w in self._workers:
            w.shutdown()
        # shutdown streams
        self.streams.stop()
        # shutdown thread pools
        self.simulated_execution.shutdown()
        self.betfair_execution.shutdown()
        # shutdown logging controls
        self.log_control(events.TerminationEvent(self))
        for c in self._logging_controls:
            if c.is_alive():
                c.join()
        # logout
        self.clients.logout()
        self._running = False
        logger.info("Exiting flumine", extra=self.info)
