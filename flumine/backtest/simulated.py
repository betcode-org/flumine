import logging
import datetime
from typing import List, Optional
from betfairlightweight.resources.bettingresources import MarketBook, RunnerBook

from .utils import (
    SimulatedPlaceResponse,
    SimulatedCancelResponse,
    SimulatedUpdateResponse,
)
from ..utils import get_price, wap
from ..order.ordertype import OrderTypes
from .. import config

logger = logging.getLogger(__name__)


class Simulated:
    """
    Class to hold `simulated` order
    matching and status.
    """

    def __init__(self, order):
        self.order = order
        self.size_matched = 0
        self.average_price_matched = 0
        self.matched = []  # [[publishTime, price, size]..]
        self.size_cancelled = 0.0
        self.size_lapsed = 0.0
        self.size_voided = 0.0
        self.market_version = None  # version at place so we can lapse if needed
        self._piq = 0.0
        self._bsp_reconciled = False

    def __call__(self, market_book: MarketBook, runner_analytics) -> None:
        # simulates order matching
        if (
            self._bsp_reconciled is False
            and market_book.bsp_reconciled
            and self.take_sp
        ):
            runner = self._get_runner(market_book)
            self._process_sp(market_book.publish_time_epoch, runner)

        elif (
            self.order.order_type.ORDER_TYPE == OrderTypes.LIMIT and self.size_remaining
        ):
            if market_book.version != self.market_version:
                self.market_version = market_book.version  # update for next time
                if market_book.status == "SUSPENDED":  # Material change
                    if self.order.order_type.persistence_type == "LAPSE":
                        self.size_lapsed += self.size_remaining
                        return

            # todo estimated piq cancellations
            self._process_traded(
                market_book.publish_time_epoch, runner_analytics.traded
            )

    def place(
        self, order_package, market_book: MarketBook, instruction: dict, bet_id: int
    ) -> SimulatedPlaceResponse:
        # simulates placeOrder request->matching->response
        # todo instruction/fillkill/timeInForce etc
        # validate market status
        if market_book.status != "OPEN":
            self.size_voided += self.size_remaining
            return self._create_place_response(
                None,
                status="FAILURE",
                error_code="ERROR_IN_ORDER",
            )

        # validate market version
        self.market_version = market_book.version
        if (
            order_package.market_version
            and order_package.market_version["version"] != self.market_version
        ):
            self.size_voided += self.size_remaining
            return self._create_place_response(
                None,
                status="FAILURE",
                error_code="ERROR_IN_ORDER",
            )

        runner = self._get_runner(market_book)
        # validate runner status
        if runner.status == "REMOVED":
            self.size_voided += self.size_remaining
            return self._create_place_response(
                None,
                status="FAILURE",
                error_code="RUNNER_REMOVED",
            )
        if self.order.order_type.ORDER_TYPE == OrderTypes.LIMIT:
            available_to_back = get_price(runner.ex.available_to_back, 0) or 1.01
            available_to_lay = get_price(runner.ex.available_to_lay, 0) or 1000
            price = self.order.order_type.price
            size = self.order.order_type.size
            if self.order.side == "BACK":
                if (
                    not order_package.client.best_price_execution
                    and available_to_back > price
                ):
                    self.size_lapsed += self.size_remaining
                    return self._create_place_response(
                        None,
                        status="FAILURE",
                        error_code="BET_LAPSED_PRICE_IMPROVEMENT_TOO_LARGE",
                    )
                elif available_to_back >= price:
                    self._process_price_matched(
                        market_book.publish_time_epoch,
                        price,
                        size,
                        runner.ex.available_to_back,
                    )
                    return self._create_place_response(bet_id)
                available = runner.ex.available_to_lay
            else:
                if (
                    not order_package.client.best_price_execution
                    and available_to_lay < price
                ):
                    self.size_lapsed += self.size_remaining
                    return self._create_place_response(
                        None,
                        status="FAILURE",
                        error_code="BET_LAPSED_PRICE_IMPROVEMENT_TOO_LARGE",
                    )
                elif available_to_lay <= price:
                    self._process_price_matched(
                        market_book.publish_time_epoch,
                        price,
                        size,
                        runner.ex.available_to_lay,
                    )
                    return self._create_place_response(bet_id)
                available = runner.ex.available_to_back

            # calculate position in queue
            for avail in available:
                if avail["price"] == price:
                    self._piq = avail["size"]
                    break

            logger.debug(
                "Simulated order {0} PIQ: {1}".format(self.order.id, self._piq)
            )
            return self._create_place_response(bet_id)
        else:
            # validate BSP available, not reconciled and market not inplay
            if (
                market_book.market_definition.bsp_market is False
                or market_book.bsp_reconciled is True
                or market_book.inplay is True
            ):
                self.size_voided += self.size_remaining
                return self._create_place_response(
                    None,
                    status="FAILURE",
                    error_code="MARKET_NOT_OPEN_FOR_BSP_BETTING",
                )
            return self._create_place_response(bet_id)

    def _create_place_response(
        self,
        bet_id: Optional[int],
        status: str = "SUCCESS",
        order_status: str = None,
        error_code: str = None,
    ) -> SimulatedPlaceResponse:
        if order_status is None:
            if self.size_remaining == 0:
                order_status = "EXECUTION_COMPLETE"
            else:
                order_status = "EXECUTABLE"
        return SimulatedPlaceResponse(
            status=status,
            order_status=order_status,
            bet_id=str(bet_id),
            average_price_matched=self.average_price_matched,
            size_matched=self.size_matched,
            placed_date=datetime.datetime.utcnow(),
            error_code=error_code,
        )

    def cancel(self, market_book: MarketBook) -> SimulatedCancelResponse:
        # simulates cancelOrder request->cancel->response
        if market_book.status != "OPEN":
            return SimulatedCancelResponse(
                status="FAILURE",
                error_code="ERROR_IN_ORDER",
            )
        if self.order.order_type.ORDER_TYPE == OrderTypes.LIMIT:
            _size_reduction = (
                self.order.update_data.get("size_reduction") or self.size_remaining
            )
            _size_cancelled = min(
                _size_reduction, self.size_remaining
            )  # cancelled cannot be more than remaining (does not error)
            self.size_cancelled += _size_cancelled
            return SimulatedCancelResponse(
                status="SUCCESS",  # todo handle errors
                size_cancelled=_size_cancelled,
                cancelled_date=datetime.datetime.utcnow(),
            )
        else:
            return SimulatedCancelResponse(
                status="FAILURE",
                error_code="BET_ACTION_ERROR",
            )

    def update(
        self, market_book: MarketBook, instruction: dict
    ) -> SimulatedUpdateResponse:
        # simulates updateOrder request->update->response
        if market_book.status != "OPEN":
            return SimulatedUpdateResponse(
                status="FAILURE",
                error_code="ERROR_IN_ORDER",
            )
        # validate BSP available
        if market_book.market_definition.persistence_enabled is False:
            return SimulatedUpdateResponse(
                status="FAILURE",
                error_code="INVALID_PERSISTENCE_TYPE",
            )
        if (
            self.order.order_type.ORDER_TYPE == OrderTypes.LIMIT
            and self.size_remaining > 0
        ):
            self.order.order_type.persistence_type = instruction.get(
                "newPersistenceType"
            )
            return SimulatedUpdateResponse(status="SUCCESS")
        else:
            return SimulatedUpdateResponse(
                status="FAILURE",
                error_code="BET_ACTION_ERROR",
            )

    def _get_runner(self, market_book: MarketBook) -> RunnerBook:
        runner_dict = {
            (runner.selection_id, runner.handicap): runner
            for runner in market_book.runners
        }
        return runner_dict.get((self.order.selection_id, self.order.handicap))

    def _process_price_matched(
        self, publish_time: int, price: float, size: float, available: list
    ) -> None:
        # calculate matched on execution
        size_remaining = size
        for avail in available:
            if size_remaining == 0:
                break
            elif (self.side == "BACK" and price <= avail["price"]) or (
                self.side == "LAY" and price >= avail["price"]
            ):
                _size_remaining = size_remaining
                size_remaining = max(size_remaining - avail["size"], 0)
                if size_remaining == 0:
                    _size_matched = _size_remaining
                else:
                    _size_matched = avail["size"]
                _matched = [publish_time, avail["price"], round(_size_matched, 2)]
                self._update_matched(_matched)
            else:
                break

    def _process_sp(self, publish_time: int, runner: RunnerBook) -> None:
        # calculate matched on BSP reconciliation
        actual_sp = runner.sp.actual_sp
        if actual_sp:
            self._bsp_reconciled = True
            _order_type = self.order.order_type
            if _order_type.ORDER_TYPE == OrderTypes.LIMIT:
                if self.side == "BACK":
                    size = self.size_remaining
                else:
                    remaining_risk = (_order_type.price - 1.0) * self.size_remaining
                    client = self.order.trade.client
                    if remaining_risk >= client.min_bsp_liability:
                        size = round(remaining_risk / (actual_sp - 1.0), 2)
                        # Cancel remaining size
                        self.size_cancelled += round(self.size_remaining - size, 2)
                    else:  # lapse
                        self.size_lapsed += self.size_remaining
                        self.order.execution_complete()
                        return
            elif _order_type.ORDER_TYPE == OrderTypes.LIMIT_ON_CLOSE:
                if self.side == "BACK":
                    if actual_sp < _order_type.price:
                        self.order.execution_complete()
                        return
                    size = _order_type.liability
                else:
                    if actual_sp > _order_type.price:
                        self.order.execution_complete()
                        return
                    size = round(
                        _order_type.liability / (actual_sp - 1), 2
                    )  # todo round 2dp down
            elif _order_type.ORDER_TYPE == OrderTypes.MARKET_ON_CLOSE:
                if self.side == "BACK":
                    size = _order_type.liability
                else:
                    size = round(_order_type.liability / (actual_sp - 1), 2)
            else:
                raise NotImplementedError()
            self._update_matched([publish_time, actual_sp, size])
            self.order.execution_complete()
        else:
            logger.warning(
                "SP not available for order {0} on runner {1}".format(
                    self.order.id, runner.selection_id
                )
            )

    def _process_traded(self, publish_time: int, traded: dict) -> None:
        # calculate matched on MarketBook update
        price = self.order.order_type.price
        for traded_price, traded_size in traded.items():
            logger.debug(
                "Simulated order {0} traded: {1} - {2}".format(
                    self.order.id, traded_price, traded_size
                )
            )
            if self.side == "BACK" and traded_price >= price:
                self._calculate_process_traded(publish_time, traded_size)
            elif self.side == "LAY" and traded_price <= price:
                self._calculate_process_traded(publish_time, traded_size)

    def _calculate_process_traded(self, publish_time: int, traded_size: float) -> None:
        traded_size = traded_size / 2
        if self._piq - traded_size < 0:
            size = traded_size - self._piq
            size = round(min(self.size_remaining, size), 2)
            if size:
                self._update_matched(
                    [
                        publish_time,
                        self.order.order_type.price,
                        size,
                    ]  # todo takes the worst price, i.e what was asked
                )
            self._piq = 0
        else:
            self._piq -= traded_size
            logger.debug(
                "Simulated order {0} PIQ: {1}".format(self.order.id, self._piq)
            )

    @property
    def take_sp(self) -> bool:
        if self.order.order_type.ORDER_TYPE == OrderTypes.LIMIT:
            if self.order.order_type.persistence_type == "MARKET_ON_CLOSE":
                return True
            return False
        else:
            return True

    @property
    def side(self) -> str:
        return self.order.side

    def _update_matched(self, data: List) -> None:
        logger.debug("Simulated order {0} matched: {1}".format(self.order.id, data))
        self.matched.append(data)
        self.size_matched, self.average_price_matched = wap(self.matched)

    @property
    def size_remaining(self) -> float:
        if self.order.order_type.ORDER_TYPE == OrderTypes.LIMIT:
            return round(
                self.order.order_type.size
                - self.size_matched
                - self.size_cancelled
                - self.size_lapsed
                - self.size_voided,
                2,
            )
        else:
            return 0.0

    @property
    def profit(self) -> float:
        if self.order.runner_status == "WINNER":
            number_of_dead_heat_winners = self.order.number_of_dead_heat_winners or 1
            profit = (self.size_matched / number_of_dead_heat_winners) * (
                self.average_price_matched - 1
            )

            if number_of_dead_heat_winners == 2:
                profit = profit - (self.size_matched / number_of_dead_heat_winners)
            elif number_of_dead_heat_winners > 2:
                profit = profit - (
                    self.size_matched
                    * (number_of_dead_heat_winners - 1)
                    / number_of_dead_heat_winners
                )

            if self.side == "LAY":
                profit = -profit

            return round(profit, 2)
        elif self.order.runner_status == "LOSER":
            if self.side == "BACK":
                return -self.size_matched
            else:
                return self.size_matched
        else:
            return 0.0

    @property
    def status(self) -> str:
        if self.take_sp:
            if self._bsp_reconciled:
                return "EXECUTION_COMPLETE"
            else:
                return "EXECUTABLE"
        else:
            if self.size_remaining:
                return "EXECUTABLE"
            else:
                return "EXECUTION_COMPLETE"

    @property
    def info(self) -> dict:
        return {
            "profit": self.profit,
            "piq": self._piq,
            "matched": self.matched,
        }

    def __bool__(self):
        return config.simulated or self.order.trade.client.paper_trade
