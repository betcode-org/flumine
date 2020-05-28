import logging
from collections import defaultdict
from betfairlightweight.resources.bettingresources import RunnerBook

from ..order.order import OrderStatus

logger = logging.getLogger(__name__)


class Middleware:
    def __call__(self, market) -> None:
        raise NotImplementedError


class SimulatedMiddleware(Middleware):
    """
    Calculates matched amounts per runner
    to be used in simulated matching.
    # todo runner removal fucks everything
    # todo currency fluctuations fucks everything
    """

    def __init__(self):
        # {marketId: {(selectionId, handicap): RunnerAnalytics}}
        self.markets = defaultdict(dict)

    def __call__(self, market) -> None:
        market_analytics = self.markets[market.market_id]
        for runner in market.market_book.runners:
            if runner.status == "ACTIVE":
                self._process_runner(market_analytics, runner)
        market.context["simulated"] = market_analytics
        # process simulated orders
        self._process_simulated_orders(market, market_analytics)

    @staticmethod
    def _process_simulated_orders(market, market_analytics: dict) -> None:
        for order in market.blotter:
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
        self.traded = {}
        self._traded_volume = []  # runner.ex.traded_volume

    def __call__(self, runner: RunnerBook):
        self.traded = self._calculate_traded(runner)
        self._traded_volume = runner.ex.traded_volume
        self._runner = runner

    def _calculate_traded(self, runner: RunnerBook) -> dict:
        if self._traded_volume == {}:
            return {}
        elif self._traded_volume == runner.ex.traded_volume:
            return {}
        else:
            c_v, p_v, traded_dictionary = {}, {}, {}
            # create dictionaries
            for i in runner.ex.traded_volume:
                c_v[i["price"]] = i["size"]
            for i in self._traded_volume:
                p_v[i["price"]] = i["size"]
            # calculate difference
            for key in c_v.keys():
                if key in p_v:
                    new_value = float(c_v[key]) - float(p_v[key])
                else:
                    new_value = float(c_v[key])
                if new_value > 0:
                    new_value = round(new_value, 2)
                    traded_dictionary[key] = new_value
            return traded_dictionary
