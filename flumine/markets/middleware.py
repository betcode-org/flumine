import logging
from collections import defaultdict
from betfairlightweight.resources.bettingresources import RunnerBook

from ..order.order import OrderStatus, OrderTypes
from ..utils import wap

logger = logging.getLogger(__name__)

WIN_MINIMUM_ADJUSTMENT_FACTOR = 2.5
PLACE_MINIMUM_ADJUSTMENT_FACTOR = 0  # todo implement correctly (https://en-betfair.custhelp.com/app/answers/detail/a_id/406)


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
        # optimisation to only process a runner on an update
        runner_updates = self._process_streaming_update(market.market_book)

        for runner in market.market_book.runners:
            if runner.status == "ACTIVE":
                update = bool(runner.selection_id in runner_updates)
                self._process_runner(market_analytics, runner, update)
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
                            # See https://github.com/liampauling/flumine/issues/454
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
    def _process_streaming_update(market_book) -> list:
        # return list of runners that have been updated
        update = market_book.streaming_update
        if update.get("img") or update.get("marketDefinition"):
            return [runner.selection_id for runner in market_book.runners]
        else:
            return [runner["id"] for runner in update.get("rc", [])]

    @staticmethod
    def _calculate_reduction_factor(price: float, adjustment_factor: float) -> float:
        price_adjusted = round(price * (1 - (adjustment_factor / 100)), 2)
        return max(price_adjusted, 1.01)  # min: 1.01

    @staticmethod
    def _process_simulated_orders(market, market_analytics: dict) -> None:
        for order in market.blotter._live_orders:
            if order.simulated and order.status == OrderStatus.EXECUTABLE:
                runner_analytics = market_analytics[
                    (order.selection_id, order.handicap)
                ]
                order.simulated(market.market_book, runner_analytics)

    @staticmethod
    def _process_runner(
        market_analytics: dict, runner: RunnerBook, update: bool
    ) -> None:
        try:
            runner_analytics = market_analytics[(runner.selection_id, runner.handicap)]
        except KeyError:
            runner_analytics = market_analytics[
                (runner.selection_id, runner.handicap)
            ] = RunnerAnalytics(runner)
        runner_analytics(runner, update)


class RunnerAnalytics:
    def __init__(self, runner: RunnerBook):
        self._runner = runner
        self.traded = {}  # price: size traded since last update
        self.middle = None  # middle of odds at last update
        self.matched = 0  # amount matched since last update
        self._traded_volume = runner.ex.traded_volume
        self._p_v = {
            i["price"]: i["size"] for i in runner.ex.traded_volume
        }  # cached current volume

    def __call__(self, runner: RunnerBook, update: bool):
        if update:
            self.middle = self._calculate_middle(self._runner)  # use last update
            self.matched = self._calculate_matched(runner)
            _tv = runner.ex.traded_volume
            if self._traded_volume == _tv:
                self.traded = {}
            else:
                self.traded = self._calculate_traded(_tv)
            self._traded_volume = _tv
            self._runner = runner
        else:
            self.matched = 0
            self.traded = {}

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

    @staticmethod
    def _calculate_middle(runner: RunnerBook) -> float:
        _back = runner.ex.available_to_back
        if _back:
            back = _back[0]["price"]
        else:
            back = 0
        _lay = runner.ex.available_to_lay
        if _lay:
            lay = _lay[0]["price"]
        else:
            lay = 1001
        return (float(back) + float(lay)) / 2

    def _calculate_matched(self, runner: RunnerBook) -> float:
        prev_total_matched = self._runner.total_matched or 0
        total_matched = (
            runner.total_matched or prev_total_matched
        )  # handles non-runner -> 0
        if total_matched != prev_total_matched:
            return round(total_matched - prev_total_matched, 2)
        else:
            return 0.0
