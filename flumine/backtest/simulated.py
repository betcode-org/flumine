import datetime
from betfairlightweight.resources.bettingresources import MarketBook, RunnerBook

from .utils import (
    SimulatedPlaceResponse,
    SimulatedCancelResponse,
    SimulatedUpdateResponse,
)
from ..utils import get_price, wap
from ..order.ordertype import OrderTypes
from .. import config


class Simulated:
    """
    Class to hold `simulated` order
    matching and status.
    """

    def __init__(self, order):
        self.order = order
        self.matched = []
        self.size_cancelled = 0.0
        self.size_lapsed = 0.0
        self.size_voided = 0.0
        self._piq = 0.0
        self._bsp_reconciled = False
        # todo handle limit lapsing

    def __call__(self, market_book: MarketBook, runner_analytics):
        # simulates order matching
        runner = self._get_runner(market_book)
        if (
            self._bsp_reconciled is False
            and market_book.bsp_reconciled
            and self.take_sp
        ):
            self._process_sp(runner)

        if self.order.order_type.ORDER_TYPE == OrderTypes.LIMIT and self.size_remaining:
            # todo piq cancellations
            self._process_traded(runner_analytics.traded)

    def place(
        self, market_book: MarketBook, instruction: dict, bet_id: int
    ) -> SimulatedPlaceResponse:
        # simulates placeOrder request->matching->response
        # todo instruction/fillkill/timeInForce/BPE etc
        if self.order.order_type.ORDER_TYPE == OrderTypes.LIMIT:
            runner = self._get_runner(market_book)
            available_to_back = get_price(runner.ex.available_to_back, 0) or 1.01
            available_to_lay = get_price(runner.ex.available_to_lay, 0) or 1000
            price = self.order.order_type.price
            size = self.order.order_type.size
            if self.order.side == "BACK":
                if available_to_back >= price:
                    self._process_price_matched(
                        price, size, runner.ex.available_to_back
                    )
                    return self._create_place_response(bet_id)
                available = runner.ex.available_to_lay
            else:
                if available_to_lay <= price:
                    self._process_price_matched(price, size, runner.ex.available_to_lay)
                    return self._create_place_response(bet_id)
                available = runner.ex.available_to_back

            # calculate position in queue
            for avail in available:
                if avail["price"] == price:
                    self._piq = avail["size"]
                    break

            return self._create_place_response(bet_id)
        else:
            return self._create_place_response(bet_id)

    def _create_place_response(
        self, bet_id: int, status: str = "SUCCESS", error_code: str = None
    ) -> SimulatedPlaceResponse:
        return SimulatedPlaceResponse(
            status=status,
            order_status="EXECUTABLE",  # todo?
            bet_id=str(bet_id),
            average_price_matched=self.average_price_matched,
            size_matched=self.size_matched,
            placed_date=datetime.datetime.utcnow(),
            error_code=error_code,
        )

    def cancel(self) -> SimulatedCancelResponse:
        # simulates cancelOrder request->cancel->response
        if self.order.order_type.ORDER_TYPE == OrderTypes.LIMIT:
            self.size_cancelled = self.size_remaining
            return SimulatedCancelResponse(
                status="SUCCESS",  # todo handle errors
                size_cancelled=self.size_cancelled,
                cancelled_date=datetime.datetime.utcnow(),
            )
        else:
            return SimulatedCancelResponse(
                status="FAILURE", error_code="BET_ACTION_ERROR",  # todo ?
            )

    def update(self, instruction: dict):
        # simulates updateOrder request->update->response
        if (
            self.order.order_type.ORDER_TYPE == OrderTypes.LIMIT
            and self.size_remaining > 0
        ):
            self.order.order_type.persistence_type = instruction.get(
                "newPersistenceType"
            )
            return SimulatedUpdateResponse(status="SUCCESS")
        else:
            return SimulatedCancelResponse(
                status="FAILURE", error_code="BET_ACTION_ERROR",
            )

    def _get_runner(self, market_book: MarketBook) -> RunnerBook:
        runner_dict = {
            (runner.selection_id, runner.handicap): runner
            for runner in market_book.runners
        }
        return runner_dict.get((self.order.selection_id, self.order.handicap))

    def _process_price_matched(
        self, price: float, size: float, available: list
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
                _matched = (avail["price"], round(_size_matched, 2))
                self.matched.append(_matched)
            else:
                break

    def _process_sp(self, runner: RunnerBook) -> None:
        # calculate matched on BSP reconciliation
        actual_sp = runner.sp.actual_sp
        if actual_sp:
            self._bsp_reconciled = True
            _order_type = self.order.order_type
            if _order_type.ORDER_TYPE == OrderTypes.LIMIT:
                size = self.size_remaining
            elif _order_type.ORDER_TYPE == OrderTypes.LIMIT_ON_CLOSE:
                if self.side == "BACK":
                    if actual_sp < _order_type.price:
                        return
                    size = _order_type.liability
                else:
                    if actual_sp > _order_type.price:
                        return
                    size = round(_order_type.liability / (actual_sp - 1), 2)
            elif _order_type.ORDER_TYPE == OrderTypes.MARKET_ON_CLOSE:
                if self.side == "BACK":
                    size = _order_type.liability
                else:
                    size = round(_order_type.liability / (actual_sp - 1), 2)
            else:
                raise NotImplementedError()
            self.matched.append((actual_sp, size))

    def _process_traded(self, traded: dict) -> None:
        # calculate matched on MarketBook update
        price = self.order.order_type.price
        for traded_price, traded_size in traded.items():
            if self.side == "BACK" and traded_price >= price:
                self._calculate_process_traded(traded_size)
            elif self.side == "LAY" and traded_price <= price:
                self._calculate_process_traded(traded_size)

    def _calculate_process_traded(self, traded_size: float) -> None:
        traded_size = traded_size / 2
        if self._piq - traded_size < 0:
            size = traded_size - self._piq
            size = round(min(self.size_remaining, size), 2)
            if size:
                self.matched.append(
                    (
                        self.order.order_type.price,
                        size,
                    )  # todo takes the worst price, i.e what was asked
                )
            self._piq = 0
        else:
            self._piq -= traded_size

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

    @property
    def average_price_matched(self) -> float:
        if self.matched:
            _, avg_price_matched = wap(self.matched)
            return avg_price_matched
        else:
            return 0

    @property
    def size_matched(self) -> float:
        if self.matched:
            size_matched, _ = wap(self.matched)
            return size_matched
        else:
            return 0

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
            if self.side == "BACK":
                return round((self.average_price_matched - 1) * self.size_matched, 2)
            else:
                return round((self.average_price_matched - 1) * -self.size_matched, 2)
        elif self.order.runner_status == "LOSER":
            if self.side == "BACK":
                return -self.size_matched
            else:
                return self.size_matched
        else:
            return 0.0

    def __bool__(self):
        return config.simulated
