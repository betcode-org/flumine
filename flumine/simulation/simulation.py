import logging
from collections import defaultdict

from .utils import SimulatedDateTime
from ..baseflumine import BaseFlumine
from ..clients import BaseClient
from ..events import events
from .. import utils
from ..exceptions import RunError
from ..order.order import OrderTypes

logger = logging.getLogger(__name__)


class FlumineSimulation(BaseFlumine):
    """
    Single threaded implementation of flumine
    for simulating strategies with betfair
    historic (or self recorded) streaming data.
    """

    SIMULATED = True

    def __init__(self, client: BaseClient = None):
        super(FlumineSimulation, self).__init__(client)
        self.simulated_datetime = SimulatedDateTime()
        self.handler_queue = []

    def run(self) -> None:
        if not self.clients.simulated:
            raise RunError(
                "Incorrect client provided, only a Simulated client can be used when simulating"
            )
        with self:
            with self.simulated_datetime:
                """
                list of either single stream or complete events depending
                on event_processing flag:
                   single: {None: [<Stream 1>], [<Stream 2>, ..]}
                   event: {123: [<Stream 1>, <Stream 2>, ..], 456: [..]}
                Event data to be muxed/processed chronologically as per
                live rather than single which is per market in isolation.
                """
                event_group_streams = defaultdict(list)  # event_group: [<Stream>, ..]
                for stream in self.streams:
                    # stream.event_group is None if stream is added without
                    # event_processing=True
                    event_group_streams[stream.event_group].append(stream)

                for event_group, streams in event_group_streams.items():
                    if event_group and len(streams) > 1:
                        logger.info(
                            "Starting historical event group '%s'",
                            event_group,
                            extra={"markets": [s.market_filter for s in streams]},
                        )
                        self.simulated_datetime.reset_real_datetime()
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
                            self._process_market_books(
                                events.MarketBookEvent(market_book)
                            )
                            # gen next
                            try:
                                market_book = next(stream_gen)
                            except StopIteration:
                                continue
                            publish_time_epoch = market_book[0].publish_time_epoch
                            # add back
                            cycles.append([publish_time_epoch, market_book, stream_gen])
                        self.handler_queue.clear()
                        logger.info(
                            "Completed historical event group '%s'", event_group
                        )
                    else:
                        for stream in streams:
                            logger.info(
                                "Starting historical market '%s'",
                                stream.market_filter,
                                extra={"market": stream.market_filter},
                            )
                            self.simulated_datetime.reset_real_datetime()
                            stream_gen = stream.create_generator()
                            for event in stream_gen():
                                self._process_market_books(
                                    events.MarketBookEvent(event)
                                )
                            self.handler_queue.clear()
                            logger.info(
                                "Completed historical market '%s'", stream.market_filter
                            )
        logger.info("Simulation complete")  # Call this after self.__exit__

    def _process_market_books(self, event: events.MarketBookEvent) -> None:
        # todo DRY!
        for market_book in event.event:
            market_id = market_book.market_id
            self.simulated_datetime(market_book.publish_time)

            # check if there are orders to process (limited to current market only)
            if self.handler_queue:
                self._check_pending_packages(market_id)

            if market_book.status == "CLOSED":
                self._process_close_market(event=events.CloseMarketEvent(market_book))
                continue

            # get market
            market = self.markets.markets.get(market_id)
            market_is_new = market is None
            if market_is_new:
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
            if market.blotter.active:
                self._process_simulated_orders(market)

            for strategy in self.strategies:
                if market_book.streaming_unique_id in strategy.stream_ids:
                    if market_is_new:
                        utils.call_strategy_error_handling(
                            strategy.process_new_market, market, market_book
                        )
                    if utils.call_strategy_error_handling(
                        strategy.check_market_book, market, market_book
                    ):
                        utils.call_strategy_error_handling(
                            strategy.process_market_book, market, market_book
                        )

    def process_order_package(self, order_package) -> None:
        # place in pending list (wait for latency+delay)
        self.handler_queue.append(order_package)

    def _process_simulated_orders(self, market) -> None:
        """Remove order from blotter live
        orders if complete and process
        orders through strategies
        """
        blotter = market.blotter
        for order in blotter.live_orders:
            if order.complete:
                blotter.complete_order(order)
            else:
                if order.order_type.ORDER_TYPE == OrderTypes.LIMIT:
                    if order.size_remaining == 0:
                        order.execution_complete()
                        blotter.complete_order(order)
                elif order.order_type.ORDER_TYPE in [
                    OrderTypes.LIMIT_ON_CLOSE,
                    OrderTypes.MARKET_ON_CLOSE,
                ]:
                    if order.current_order.status == "EXECUTION_COMPLETE":
                        order.execution_complete()
                        blotter.complete_order(order)
        for strategy in self.strategies:
            strategy_orders = blotter.strategy_orders(strategy)
            if strategy_orders:
                utils.call_process_orders_error_handling(
                    strategy, market, strategy_orders
                )

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

    def __repr__(self) -> str:
        return "<FlumineSimulation>"

    def __str__(self) -> str:
        return "<FlumineSimulation>"
