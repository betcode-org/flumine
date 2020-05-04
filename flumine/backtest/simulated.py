import datetime
from typing import Tuple
from betfairlightweight.resources.bettingresources import MarketBook, RunnerBook

from .utils import SimulatedPlaceResponse
from ..utils import get_price
from ..order.ordertype import OrderTypes


class Simulated:
    def __init__(self, order):
        self.order = order
        self.matched = []

    def __call__(self, *args, **kwargs):
        pass

    def place(
        self, market_book: MarketBook, instruction: dict, bet_id: int
    ) -> SimulatedPlaceResponse:
        # todo instruction/fillkill/timeInForce/BPE etc
        if self.order.order_type.ORDER_TYPE == OrderTypes.LIMIT:
            runner = self._get_runner(market_book)
            available_to_back = get_price(runner.ex.available_to_back, 0) or 1.01
            available_to_lay = get_price(runner.ex.available_to_lay, 0) or 1000
            price = self.order.order_type.price
            size = self.order.order_type.size
            if self.order.side == "BACK":
                # available = runner.ex.available_to_lay
                if available_to_back >= price:
                    self._process_price_matched(
                        price, size, runner.ex.available_to_back
                    )
            else:
                # available = runner.ex.available_to_back
                if available_to_lay <= price:
                    self._process_price_matched(price, size, runner.ex.available_to_lay)
            # todo on top
            return SimulatedPlaceResponse(
                status="SUCCESS",
                order_status="EXECUTABLE",
                bet_id=str(bet_id),
                average_price_matched=self.average_price_matched,
                size_matched=self.size_matched,
                placed_date=datetime.datetime.utcnow(),
                error_code=None,
            )
        else:
            raise NotImplementedError()  # todo

    def cancel(self):
        pass

    def update(self):
        pass

    def replace(self):
        pass

    def _get_runner(self, market_book: MarketBook) -> RunnerBook:
        runner_dict = {
            (runner.selection_id, runner.handicap): runner
            for runner in market_book.runners
        }
        return runner_dict.get((self.order.selection_id, self.order.handicap))

    def _process_price_matched(
        self, price: float, size: float, available: list
    ) -> None:
        size_remaining = size
        for avail in available:
            if size_remaining == 0:
                break
            elif (self.side == "BACK" and price <= avail.price) or (
                self.side == "LAY" and price >= avail.price
            ):
                _size_remaining = size_remaining
                size_remaining = max(size_remaining - avail.size, 0)
                if size_remaining == 0:
                    _size_matched = _size_remaining
                else:
                    _size_matched = avail.size
                _matched = (avail.price, _size_matched)
                self.matched.append(_matched)
            else:
                break

    @staticmethod
    def _wap(matched: list) -> Tuple[float, float]:
        if not matched:
            return 0, 0
        a, b = 0, 0
        for match in matched:
            a += match[0] * match[1]
            b += match[1]
        if b == 0 or a == 0:
            return 0, 0
        else:
            return round(b, 2), round(a / b, 2)

    @property
    def side(self) -> str:
        return self.order.side

    @property
    def average_price_matched(self) -> float:
        if self.matched:
            _, avg_price_matched = self._wap(self.matched)
            return avg_price_matched
        else:
            return 0

    @property
    def size_matched(self) -> float:
        if self.matched:
            size_matched, _ = self._wap(self.matched)
            return size_matched
        else:
            return 0
