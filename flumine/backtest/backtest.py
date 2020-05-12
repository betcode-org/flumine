import logging
import datetime

from ..baseflumine import BaseFlumine
from ..events import events
from .. import config
from ..clients import ExchangeType
from ..exceptions import RunError
from .utils import PendingPackages
from ..markets.market import Market
from ..order.orderpackage import OrderPackageType
from ..order import process

logger = logging.getLogger(__name__)


class FlumineBacktest(BaseFlumine):
    """
    Single threaded implementation of flumine
    for backtesting strategies with betfair
    historic (or self recorded) streaming data.
    """

    BACKTEST = True

    def __init__(self, client):
        super(FlumineBacktest, self).__init__(client)
        self._pending_packages = PendingPackages()

    def run(self) -> None:
        if self.client.EXCHANGE != ExchangeType.SIMULATED:
            raise RunError(
                "Incorrect client provided, only a Simulated client can be used when backtesting"
            )
        with self:
            self._monkey_patch_datetime()

            for stream in self.streams:
                stream_gen = stream.create_generator()

                logger.info(
                    "Starting historical market '{0}'".format(stream.market_filter)
                )

                for event in stream_gen():
                    if event:
                        for market_book in event:  # todo move?
                            market_book.streaming_unique_id = stream.stream_id
                        self._process_market_books(events.MarketBookEvent(event))

                self._pending_packages.clear()

                logger.info(
                    "Completed historical market '{0}'".format(stream.market_filter)
                )

            self._process_end_flumine()

            logger.info("Backtesting complete")

            self._unpatch_datetime()

    def _process_market_books(self, event: events.MarketBookEvent) -> None:
        for market_book in event.event:
            market_id = market_book.market_id
            config.current_time = market_book.publish_time

            # check if there are orders to process
            self._check_pending_packages()

            if market_book.status == "CLOSED":
                self._process_close_market(event=events.CloseMarketEvent(market_book))
                continue

            market = self.markets.markets.get(market_id)
            if not market:
                market = self._add_live_market(market_id, market_book)

            # process market
            market(market_book)

            for strategy in self.strategies:
                if strategy.check_market(market, market_book):
                    strategy.process_market_book(market, market_book)

            # process current orders
            blotter = market.blotter
            for order in blotter:
                process.process_current_order(order)
            for strategy in self.strategies:
                strategy_orders = blotter.strategy_orders(strategy)
                strategy.process_orders(market, strategy_orders)

            self._process_market_orders(market)

    def _process_market_orders(self, market: Market) -> None:
        for order_package in market.blotter.process_orders(self.client):
            self._pending_packages.append(order_package)

    def _process_order_package(self, order_package) -> None:
        """Validate trading controls and
        then execute immediately.
        """
        super(FlumineBacktest, self)._process_order_package(order_package)
        order_package.processed = True

    def _check_pending_packages(self):
        for order_package in self._pending_packages:
            _client = order_package.client
            if order_package.package_type == OrderPackageType.PLACE:
                if order_package.elapsed_seconds > (
                    _client.execution.PLACE_LATENCY + order_package.bet_delay
                ):
                    self._process_order_package(order_package)
            elif order_package.package_type == OrderPackageType.CANCEL:
                if order_package.elapsed_seconds > _client.execution.CANCEL_LATENCY:
                    self._process_order_package(order_package)
            elif order_package.package_type == OrderPackageType.UPDATE:
                if order_package.elapsed_seconds > _client.execution.UPDATE_LATENCY:
                    self._process_order_package(order_package)
            elif order_package.package_type == OrderPackageType.REPLACE:
                if order_package.elapsed_seconds > (
                    _client.execution.REPLACE_LATENCY + order_package.bet_delay
                ):
                    self._process_order_package(order_package)

    def _monkey_patch_datetime(self):
        config.current_time = datetime.datetime.utcnow()

        class NewDateTime(datetime.datetime):
            @classmethod
            def utcnow(cls):
                return config.current_time

        self._old_datetime = datetime.datetime
        datetime.datetime = NewDateTime

    def _unpatch_datetime(self):
        datetime.datetime = self._old_datetime

    def __repr__(self) -> str:
        return "<FlumineBacktest>"

    def __str__(self) -> str:
        return "<FlumineBacktest>"
