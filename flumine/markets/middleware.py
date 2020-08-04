import logging
from collections import defaultdict
from betfairlightweight.resources.bettingresources import RunnerBook

from ..order.order import OrderStatus
from ..utils import get_price, wap

logger = logging.getLogger(__name__)

WIN_MINIMUM_ADJUSTMENT_FACTOR = 2.5
PLACE_MINIMUM_ADJUSTMENT_FACTOR = 0  # todo implement correctly (https://en-betfair.custhelp.com/app/answers/detail/a_id/406)


class Middleware:
    def __call__(self, market) -> None:
        raise NotImplementedError

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
                    order.simulated.size_voided = order.order_type.size
                    logger.warning(
                        "Order voided on non runner {0}".format(order.selection_id),
                        extra=order.info,
                    )
                else:
                    if order.status == OrderStatus.EXECUTABLE:
                        # todo cancel if not PERSIST
                        # todo does a market version bump occur if withdrawal is below the limit?
                        pass
                    if (
                        removal_adjustment_factor
                        and removal_adjustment_factor >= WIN_MINIMUM_ADJUSTMENT_FACTOR
                    ):
                        # todo place market
                        for match in order.simulated.matched:
                            match[1] = round(
                                match[1] * (1 - (removal_adjustment_factor / 100)), 2
                            )
                        _, order.simulated.average_price_matched = wap(
                            order.simulated.matched
                        )
                        logger.warning(
                            "Order adjusted due to non runner {0}".format(
                                order.selection_id
                            ).format(order.selection_id),
                            extra=order.info,
                        )

    @staticmethod
    def _process_simulated_orders(market, market_analytics: dict) -> None:
        for order in market.blotter.live_orders:
            if order.simulated and order.status == OrderStatus.EXECUTABLE:
                runner_analytics = market_analytics.get(
                    (order.selection_id, order.handicap)
                )
                order.simulated(market.market_book, runner_analytics)

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
        self.traded = {}  # price: size traded since last event
        self.middle = None  # middle of odds at last event
        self.matched = 0  # amount matched since last event
        self._traded_volume = runner.ex.traded_volume

    def __call__(self, runner: RunnerBook):
        self.middle = self._calculate_middle(self._runner)  # use last event
        self.matched = self._calculate_matched(runner)
        self.traded = self._calculate_traded(runner)
        self._traded_volume = runner.ex.traded_volume
        self._runner = runner

    def _calculate_traded(self, runner: RunnerBook) -> dict:
        if self._traded_volume == runner.ex.traded_volume:
            return {}
        else:
            c_v, p_v, traded = {}, {}, {}
            # create dictionaries
            for i in runner.ex.traded_volume:
                c_v[i["price"]] = i["size"]
            for i in self._traded_volume:
                p_v[i["price"]] = i["size"]  # todo cache from previous run?
            # calculate difference
            for key in c_v.keys():
                if key in p_v:
                    new_value = float(c_v[key]) - float(p_v[key])
                else:
                    new_value = float(c_v[key])
                if new_value > 0:
                    new_value = round(new_value, 2)
                    traded[key] = new_value
            return traded

    @staticmethod
    def _calculate_middle(runner: RunnerBook) -> float:
        back = get_price(runner.ex.available_to_back, 0) or 0
        lay = get_price(runner.ex.available_to_lay, 0) or 1001
        return (float(back) + float(lay)) / 2

    def _calculate_matched(self, runner: RunnerBook) -> float:
        prev_total_matched = self._runner.total_matched or 0
        total_matched = (
            runner.total_matched or prev_total_matched
        )  # handles non-runner -> 0
        return round(total_matched - prev_total_matched, 2)
