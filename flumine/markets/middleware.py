import datetime
import logging
from betfairlightweight.resources.bettingresources import (
    MarketBook,
    MarketCatalogue,
    RunnerBook,
)

from .blotter import Blotter
from .. import config

logger = logging.getLogger(__name__)


class Middleware:
    def __call__(
        self, market_catalogue: MarketCatalogue, market_book: MarketBook
    ) -> None:
        raise NotImplementedError


class SimulatedMiddleware:
    """
    Calculates matched amounts per runner
    to be used in simulated matching.
    # todo runner removal fucks everything
    # todo currency fluctuations fucks everything
    """

    def __init__(self):
        self.runners = {}  # {(selectionId, handicap): RunnerAnalytics}

    def __call__(
        self, market_catalogue: MarketCatalogue, market_book: MarketBook
    ) -> None:
        for runner in market_book.runners:
            if runner.status == "ACTIVE":
                self._process_runner(runner)

    def _process_runner(self, runner: RunnerBook) -> None:
        try:
            runner_analytics = self.runners[(runner.selection_id, runner.handicap)]
        except KeyError:
            runner_analytics = self.runners[
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
