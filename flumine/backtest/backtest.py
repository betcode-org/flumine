import logging
import datetime

from ..baseflumine import BaseFlumine
from ..event.event import MarketBookEvent
from .. import config
from ..clients import ExchangeType
from ..exceptions import RunError

logger = logging.getLogger(__name__)


class FlumineBacktest(BaseFlumine):
    """
    Single threaded implementation of flumine
    for backtesting strategies with betfair
    historic (or self recorded) streaming data.
    """

    BACKTEST = True

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
                    for market_book in event:
                        config.current_time = market_book.publish_time
                        market_book.streaming_unique_id = stream.stream_id
                    self._process_market_books(MarketBookEvent(event))

                logger.info(
                    "Completed historical market '{0}'".format(stream.market_filter)
                )

            self._process_end_flumine()

            logger.info("Backtesting complete")

            self._unpatch_datetime()

    # todo def _process_market_books(self, event):
    #     for market_book in event.event:
    #         for strategy in self.strategies:
    #             if strategy.check_market(market_book):
    #                 strategy.process_market_book(market_book)

    # todo def _process_market_orders(self, market: Market) -> None:
    #     for order_package in market.blotter.process_orders(self.client):
    #         self.handler_queue.put(order_package)

    # todo def _process_order_package(self, order_package) -> None:
    #     """Validate trading controls and
    #     then execute.
    #     """
    #     for control in self._trading_controls:
    #         control(order_package)
    #     for control in order_package.client.trading_controls:
    #         control(order_package)
    #     if order_package.orders:
    #         order_package.client.execution.handler(order_package)
    #     else:
    #         logger.warning("Empty package, not executing", extra=order_package.info)

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
