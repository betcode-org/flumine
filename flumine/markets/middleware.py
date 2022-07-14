import os
import logging
from collections import defaultdict
from betfairlightweight.resources.bettingresources import RunnerBook

from ..order.order import OrderStatus, OrderTypes
from ..utils import wap, call_strategy_error_handling
from ..streams.historicalstream import (
    HistoricListener,
    FlumineHistoricalGeneratorStream,
)
from .. import config

logger = logging.getLogger(__name__)

WIN_MINIMUM_ADJUSTMENT_FACTOR = 2.5
PLACE_MINIMUM_ADJUSTMENT_FACTOR = 0  # todo implement correctly (https://en-betfair.custhelp.com/app/answers/detail/a_id/406)
LIVE_STATUS = [
    OrderStatus.EXECUTABLE,
    OrderStatus.CANCELLING,
    OrderStatus.UPDATING,
    OrderStatus.REPLACING,
]


class Middleware:
    def __call__(self, market) -> None:
        pass

    def add_market(self, market) -> None:
        pass

    def remove_market(self, market) -> None:
        pass


class SimulatedMiddleware(Middleware):
    """
    Calculates matched amounts per runner
    to be used in simulated matching.
    # todo currency fluctuations fucks everything
    """

    def __init__(self):
        # {marketId: {(selectionId, handicap): RunnerAnalytics}}
        self.markets = defaultdict(dict)
        self._runner_removals = []

    def __call__(self, market) -> None:
        market_analytics = self.markets[market.market_id]
        runner_removals = []  # [(selectionId, handicap, adjustmentFactor)..]

        for runner in market.market_book.runners:
            if runner.status == "ACTIVE":
                self._process_runner(market_analytics, runner)
            elif runner.status == "REMOVED":
                _removal = (
                    runner.selection_id,
                    runner.handicap,
                    runner.adjustment_factor,
                )
                if _removal not in self._runner_removals:
                    logger.warning(
                        "Runner {0} ({2}) removed from market {3}".format(
                            *_removal, market.market_id
                        )
                    )
                    self._runner_removals.append(_removal)
                    runner_removals.append(_removal)

        for _removal in runner_removals:
            self._process_runner_removal(market, *_removal)

        market.context["simulated"] = market_analytics
        # process simulated orders
        if market.blotter.active:
            self._process_simulated_orders(market, market_analytics)

    def remove_market(self, market) -> None:
        try:
            del self.markets[market.market_id]
        except KeyError:
            pass

    def _process_runner_removal(
        self,
        market,
        removal_selection_id: int,
        removal_handicap: int,
        removal_adjustment_factor: float,
    ) -> None:
        for order in market.blotter:
            if order.simulated:
                if order.lookup == (
                    market.market_id,
                    removal_selection_id,
                    removal_handicap,
                ):
                    # cancel and void order
                    order.simulated.size_matched = 0
                    order.simulated.average_price_matched = 0
                    order.simulated.matched = []
                    if order.order_type.ORDER_TYPE == OrderTypes.LIMIT:
                        order.simulated.size_voided = order.order_type.size
                    else:
                        order.simulated.size_voided = order.order_type.liability
                    logger.warning(
                        "Order voided on non runner {0}".format(order.selection_id),
                        extra=order.info,
                    )
                else:
                    # TODO: "Where an SP lay bet in a win market has a maximum odds limit specified,..."
                    if (
                        order.order_type.ORDER_TYPE == OrderTypes.MARKET_ON_CLOSE
                    ) and order.side == "LAY":
                        if market.market_type == "WIN":
                            runner = [
                                x
                                for x in market.market_book.runners
                                if x.selection_id == order.selection_id
                                and x.handicap == order.handicap
                            ][0]
                            runner_adjustment_factor = runner.adjustment_factor
                            # See https://github.com/betcode-org/flumine/issues/454
                            multiplier = 1 - (
                                removal_adjustment_factor
                                / (100 - runner_adjustment_factor)
                            )
                            order.order_type.liability *= multiplier
                            if order.average_price_matched:
                                # We will get here if the NR is declared inplay
                                order.current_order.size_matched = round(
                                    order.order_type.liability
                                    / (order.average_price_matched - 1),
                                    2,
                                )
                            logger.warning(
                                "WIN MARKET_ON_CLOSE Order adjusted due to non runner {0}".format(
                                    order.selection_id
                                ),
                                extra=order.info,
                            )
                        elif market.market_type in {"PLACE", "OTHER_PLACE"}:
                            multiplier = (100 - removal_adjustment_factor) * 0.01
                            order.order_type.liability *= multiplier
                            if order.average_price_matched:
                                # We will get here if the NR is declared inplay
                                order.current_order.size_matched = round(
                                    order.order_type.liability
                                    / (order.average_price_matched - 1),
                                    2,
                                )
                            logger.warning(
                                "PLACE MARKET_ON_CLOSE Order adjusted due to non runner {0}".format(
                                    order.selection_id
                                ),
                                extra=order.info,
                            )
                    elif (
                        removal_adjustment_factor
                        and removal_adjustment_factor >= WIN_MINIMUM_ADJUSTMENT_FACTOR
                    ):
                        # todo place market
                        for match in order.simulated.matched:
                            match[1] = self._calculate_reduction_factor(
                                match[1], removal_adjustment_factor
                            )
                        _, order.simulated.average_price_matched = wap(
                            order.simulated.matched
                        )
                        logger.warning(
                            "Order adjusted due to non runner {0}".format(
                                order.selection_id
                            ),
                            extra=order.info,
                        )

    @staticmethod
    def _calculate_reduction_factor(price: float, adjustment_factor: float) -> float:
        price_adjusted = round(price * (1 - (adjustment_factor / 100)), 2)
        return max(price_adjusted, 1.01)  # min: 1.01

    def _process_simulated_orders(self, market, market_analytics: dict) -> None:
        """
        #538 smart matching
          - isolation per order
            Potential double counting of passive liquidity, old logic no longer implemented
          - isolation per strategy (default)
            Prevent double counting of passive liquidity per strategy
          - isolation per instance
            Prevent double counting of passive liquidity on all orders regardless of strategy (interaction across strategies)
        """
        # isolation per strategy (default)
        if config.simulated_strategy_isolation:
            for strategy, orders in market.blotter._strategy_orders.items():
                live_orders = [
                    o for o in orders if o.status in LIVE_STATUS and o.simulated
                ]
                if live_orders:
                    _lookup = {k: v.traded.copy() for k, v in market_analytics.items()}
                    live_orders_sorted = self._sort_orders(live_orders)
                    for order in live_orders_sorted:
                        runner_traded = _lookup[(order.selection_id, order.handicap)]
                        order.simulated(market.market_book, runner_traded)
        else:  # isolation per instance
            live_orders = list(market.blotter.live_orders)
            if live_orders:
                _lookup = {k: v.traded.copy() for k, v in market_analytics.items()}
                live_orders_sorted = self._sort_orders(live_orders)
                for order in live_orders_sorted:
                    if order.status in LIVE_STATUS and order.simulated:
                        runner_traded = _lookup[(order.selection_id, order.handicap)]
                        order.simulated(market.market_book, runner_traded)

    @staticmethod
    def _sort_orders(orders: list) -> list:
        # order by betId (default), side (Lay,Back) and then price
        lay_orders = sorted(
            [
                o
                for o in orders
                if o.side == "LAY"
                and o.order_type.ORDER_TYPE != OrderTypes.MARKET_ON_CLOSE
            ],
            key=lambda x: -x.order_type.price,
        )
        back_orders = sorted(
            [
                o
                for o in orders
                if o.side == "BACK"
                and o.order_type.ORDER_TYPE != OrderTypes.MARKET_ON_CLOSE
            ],
            key=lambda x: x.order_type.price,
        )
        moc = [
            o for o in orders if o.order_type.ORDER_TYPE == OrderTypes.MARKET_ON_CLOSE
        ]
        return lay_orders + back_orders + moc

    @staticmethod
    def _process_runner(market_analytics: dict, runner: RunnerBook) -> None:
        try:
            runner_analytics = market_analytics[(runner.selection_id, runner.handicap)]
        except KeyError:
            runner_analytics = market_analytics[
                (runner.selection_id, runner.handicap)
            ] = RunnerAnalytics(runner)
        runner_analytics(runner)


class RunnerAnalytics:
    def __init__(self, runner: RunnerBook):
        self._runner = runner
        self.traded = {}  # price: size traded since last update
        self._traded_volume = runner.ex.traded_volume
        self._p_v = {
            i["price"]: i["size"] for i in runner.ex.traded_volume
        }  # cached current volume

    def __call__(self, runner: RunnerBook):
        _tv = runner.ex.traded_volume
        if self._traded_volume == _tv:
            self.traded = {}
        else:
            self.traded = self._calculate_traded(_tv)
            self._traded_volume = _tv
        self._runner = runner

    def _calculate_traded(self, traded_volume: list) -> dict:
        p_v, traded = self._p_v, {}
        # create dictionary
        c_v = {i["price"]: i["size"] for i in traded_volume}
        # calculate difference
        for key, value in c_v.items():
            if key in p_v:
                new_value = float(value) - float(p_v[key])
                if new_value > 0:
                    traded[key] = round(new_value, 2)
            else:
                traded[key] = value
        # cache for next update
        self._p_v = c_v
        return traded


class SimulatedSportsDataMiddleware(Middleware):
    """
    Middleware to allow simulation of historic
    sports data.
    Creates generator of sports data that is cycled
    chronologically with the MarketBooks calling
    `strategy.process_sports_data`
    """

    def __init__(self, operation: str, directory: str):
        self.operation = operation  # "cricketSubscription" or "raceSubscription"
        self.directory = directory  # sports data directory (marketId used for lookup)
        self._gen = None
        self._next = None

    def __call__(self, market) -> None:
        pt = market.market_book.publish_time_epoch
        while True:
            for update in self._next:
                if update.market_id != market.market_id:
                    continue
                if pt > update.publish_time_epoch:
                    for strategy in market.flumine.strategies:
                        if (
                            market.market_book.streaming_unique_id
                            in strategy.stream_ids
                        ):
                            call_strategy_error_handling(
                                strategy.process_sports_data, market, update
                            )
                else:
                    return
            try:
                self._next = next(self._gen)
            except StopIteration:
                break

    def add_market(self, market) -> None:
        # create sports data generator
        file_path = os.path.join(self.directory, market.market_id)
        self._gen = self._create_generator(file_path, self.operation, 123)()
        self._next = next(self._gen)

    def remove_market(self, market) -> None:
        # clear gens
        self._gen = None
        self._next = None

    @staticmethod
    def _create_generator(file_path: str, operation: str, unique_id: int):
        listener = HistoricListener(max_latency=None, update_clk=False)
        stream = FlumineHistoricalGeneratorStream(
            file_path=file_path,
            listener=listener,
            operation=operation,
            unique_id=unique_id,
        )
        return stream.get_generator()
