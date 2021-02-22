import logging
from typing import Iterable
from collections import defaultdict

from ..order.ordertype import OrderTypes
from ..utils import (
    calculate_unmatched_exposure,
    calculate_matched_exposure,
)
from ..order.order import BaseOrder, OrderStatus

logger = logging.getLogger(__name__)

# https://www.betfair.com/aboutUs/Betfair.Charges/#charges6
IMPLIED_COMMISSION_RATE = 0.03


class Blotter:

    """
    Simple and fast class to hold all orders for
    a particular market.

    `customer_order_ref` used as the key and various
    caches available for faster access.

        blotter["abc"] = <Order>  # set
        "abc" in blotter  # contains
        orders = [o for o in blotter]  # iter
        order = blotter["abc"]  # get
    """

    def __init__(self, market_id: str):
        self.market_id = market_id
        self._orders = {}  # {Order.id: Order}
        self._live_orders = []  # cached list of live orders
        self._strategy_orders = defaultdict(
            list
        )  # cache list per strategy (faster lookup)

    def strategy_orders(self, strategy) -> list:
        """Returns all orders related to a strategy."""
        return self._strategy_orders[strategy]

    @property
    def live_orders(self):
        return iter(self._live_orders)

    @property
    def has_live_orders(self) -> bool:
        return bool(self._live_orders)

    def process_closed_market(self, market_book) -> None:
        for order in self:
            for runner in market_book.runners:
                if (order.selection_id, order.handicap) == (
                    runner.selection_id,
                    runner.handicap,
                ):
                    order.runner_status = runner.status

    def process_cleared_orders(self, cleared_orders) -> list:
        # todo update order.cleared?
        return [order for order in self]

    """ position """

    def selection_exposure(self, strategy, lookup: tuple) -> float:
        """Returns strategy/selection exposure, which is the worse-case loss arising
        from the selection either winning or losing. Can be positive or zero.
            positive = potential loss
            zero = no potential loss
        """
        mb, ml = [], []  # matched bets, (price, size)
        ub, ul = [], []  # unmatched bets, (price, size)
        moc_win_liability = 0.0
        moc_lose_liability = 0.0
        for order in self.strategy_orders(strategy):
            if order.lookup == lookup:
                if order.status == OrderStatus.VIOLATION:
                    continue

                if order.order_type.ORDER_TYPE == OrderTypes.LIMIT:
                    _size_matched = order.size_matched  # cache
                    if _size_matched:
                        if order.side == "BACK":
                            mb.append((order.average_price_matched, _size_matched))
                        else:
                            ml.append((order.average_price_matched, _size_matched))
                    _size_remaining = order.size_remaining  # cache
                    if order.order_type.price and _size_remaining:
                        if order.side == "BACK":
                            ub.append((order.order_type.price, _size_remaining))
                        else:
                            ul.append((order.order_type.price, _size_remaining))
                elif order.order_type.ORDER_TYPE in (
                    OrderTypes.LIMIT_ON_CLOSE,
                    OrderTypes.MARKET_ON_CLOSE,
                ):
                    if order.side == "BACK":
                        moc_lose_liability -= order.order_type.liability
                    else:
                        moc_win_liability -= order.order_type.liability
                else:
                    raise ValueError(
                        "Unexpected order type: %s" % order.order_type.ORDER_TYPE
                    )

        matched_exposure = calculate_matched_exposure(mb, ml)
        unmatched_exposure = calculate_unmatched_exposure(ub, ul)

        worst_possible_profit_on_win = (
            matched_exposure[0] + unmatched_exposure[0] + moc_win_liability
        )
        worst_possible_profit_on_lose = (
            matched_exposure[1] + unmatched_exposure[1] + moc_lose_liability
        )
        exposure = -min(worst_possible_profit_on_win, worst_possible_profit_on_lose)
        return max(exposure, 0.0)

    """ getters / setters """

    def complete_order(self, order) -> None:
        self._live_orders.remove(order)

    def has_order(self, customer_order_ref: str) -> bool:
        return customer_order_ref in self._orders

    __contains__ = has_order

    def __setitem__(self, customer_order_ref: str, order) -> None:
        self._orders[customer_order_ref] = order
        self._live_orders.append(order)
        self._strategy_orders[order.trade.strategy].append(order)

    def __getitem__(self, customer_order_ref: str):
        return self._orders[customer_order_ref]

    def __iter__(self) -> Iterable[BaseOrder]:
        return iter(list(self._orders.values()))

    def __len__(self) -> int:
        return len(self._orders)
