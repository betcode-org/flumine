import logging
import datetime
from collections import defaultdict

from ..baseflumine import BaseFlumine
from ..events import events
from .. import config, utils
from ..clients import ExchangeType
from ..exceptions import RunError
from ..order.trade import TradeStatus
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
        self.handler_queue = []

    def run(self) -> None:
        if self.client.EXCHANGE != ExchangeType.SIMULATED:
            raise RunError(
                "Incorrect client provided, only a Simulated client can be used when backtesting"
            )
        with self:
            self._monkey_patch_datetime()
            """
            list of either single stream or complete events depending 
            on event_processing flag:
               single: {None: [<Stream 1>], [<Stream 2>, ..]}
               event: {123: [<Stream 1>, <Stream 2>, ..], 456: [..]}
            Event data to be muxed/processed chronologically as per 
            live rather than single which is per market in isolation.
            """
            event_streams = defaultdict(list)  # eventId: [<Stream>, ..]
            for stream in self.streams:
                event_id = stream.event_id if stream.event_processing else None
                event_streams[event_id].append(stream)

            for event_id, streams in event_streams.items():
                if event_id and len(streams) > 1:
                    logger.info(
                        "Starting historical event '{0}'".format(event_id),
                        extra={
                            "event_id": event_id,
                            "markets": [s.market_filter for s in streams],
                        },
                    )
                    # create cycles
                    cycles = []  # [[epoch, [MarketBook], gen], ..]
                    for stream in streams:
                        stream_gen = stream.create_generator()()
                        market_book = next(stream_gen)
                        publish_time_epoch = market_book[0].publish_time_epoch
                        cycles.append([publish_time_epoch, market_book, stream_gen])
                    # process cycles
                    while cycles:
                        # order by epoch
                        cycles.sort(key=lambda x: x[0])
                        # get current
                        _, market_book, stream_gen = cycles.pop(0)
                        # process current
                        self._process_market_books(events.MarketBookEvent(market_book))
                        # gen next
                        try:
                            market_book = next(stream_gen)
                        except StopIteration:
                            continue
                        publish_time_epoch = market_book[0].publish_time_epoch
                        # add back
                        cycles.append([publish_time_epoch, market_book, stream_gen])
                    self.handler_queue.clear()
                    logger.info("Completed historical event '{0}'".format(event_id))
                else:
                    for stream in streams:
                        logger.info(
                            "Starting historical market '{0}'".format(
                                stream.market_filter
                            ),
                            extra={
                                "market": stream.market_filter,
                            },
                        )
                        stream_gen = stream.create_generator()
                        for event in stream_gen():
                            self._process_market_books(events.MarketBookEvent(event))
                        self.handler_queue.clear()
                        logger.info(
                            "Completed historical market '{0}'".format(
                                stream.market_filter
                            )
                        )

            self._process_end_flumine()

            logger.info("Backtesting complete")

            self._unpatch_datetime()

    def _process_market_books(self, event: events.MarketBookEvent) -> None:
        # todo DRY!
        for market_book in event.event:
            market_id = market_book.market_id
            config.current_time = market_book.publish_time

            # check if there are orders to process (limited to current market only)
            if self.handler_queue:
                self._check_pending_packages(market_id)

            if market_book.status == "CLOSED":
                self._process_close_market(event=events.CloseMarketEvent(market_book))
                continue

            # get market
            market = self.markets.markets.get(market_id)
            if market is None:
                market = self._add_market(market_id, market_book)
                self.log_control(events.MarketEvent(market))
            elif market.closed:
                self.markets.add_market(market_id, market)

            # process market
            market(market_book)

            # process middleware
            for middleware in self._market_middleware:
                utils.call_middleware_error_handling(middleware, market)

            # process current orders
            self._process_backtest_orders(market)

            for strategy in self.strategies:
                if utils.call_strategy_error_handling(
                    strategy.check_market, market, market_book
                ):
                    utils.call_strategy_error_handling(
                        strategy.process_market_book, market, market_book
                    )

    def process_order_package(self, order_package) -> None:
        # place in pending list (wait for latency+delay)
        self.handler_queue.append(order_package)

    def _process_backtest_orders(self, market) -> None:
        """Remove order from blotter live
        orders if complete and process
        orders through strategies
        """
        blotter = market.blotter
        for order in blotter.live_orders:
            process.process_current_order(order)
            if order.trade.status == TradeStatus.COMPLETE:
                blotter.complete_order(order)
        for strategy in self.strategies:
            strategy_orders = blotter.strategy_orders(strategy)
            utils.call_process_orders_error_handling(strategy, market, strategy_orders)

    def _check_pending_packages(self, market_id: str) -> None:
        processed = []
        for order_package in self.handler_queue:
            if (
                order_package.market_id == market_id
                and order_package.elapsed_seconds > order_package.simulated_delay
            ):
                order_package.client.execution.handler(order_package)
                processed.append(order_package)
        for p in processed:
            self.handler_queue.remove(p)

    def _monkey_patch_datetime(self) -> None:
        config.current_time = datetime.datetime.utcnow()

        class NewDateTime(datetime.datetime):
            @classmethod
            def utcnow(cls):
                return config.current_time

        self._old_datetime = datetime.datetime
        datetime.datetime = NewDateTime

    def _unpatch_datetime(self) -> None:
        datetime.datetime = self._old_datetime

    def __repr__(self) -> str:
        return "<FlumineBacktest>"

    def __str__(self) -> str:
        return "<FlumineBacktest>"
