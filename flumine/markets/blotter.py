import logging
from typing import Iterable

from ..order.ordertype import OrderTypes
from ..utils import (
    batch_orders,
    chunks,
    calculate_unmatched_exposure,
    calculate_matched_exposure,
)
from ..order.order import BaseOrder, OrderStatus
from ..order.orderpackage import OrderPackageType, BetfairOrderPackage

logger = logging.getLogger(__name__)

# https://www.betfair.com/aboutUs/Betfair.Charges/#charges6
IMPLIED_COMMISSION_RATE = 0.03


class Blotter:
    def __init__(self, market_id: str):
        self.market_id = market_id
        self._orders = {}  # {Order.id: Order}
        self._live_orders = []  # cached list of live orders
        # pending orders, list of (<Order>, {..})
        self.pending_place = []
        self.pending_cancel = []
        self.pending_update = []
        self.pending_replace = []

    def strategy_orders(self, strategy) -> list:
        """Returns all orders related to a strategy."""
        return [order for order in self if order.trade.strategy == strategy]

    def process_orders(self, client, bet_delay: int = 0) -> list:
        packages = []
        if self.pending_place:
            packages += self._create_packages(
                client, self.pending_place, OrderPackageType.PLACE, bet_delay
            )
        if self.pending_cancel:
            packages += self._create_packages(
                client, self.pending_cancel, OrderPackageType.CANCEL, bet_delay
            )
        if self.pending_update:
            packages += self._create_packages(
                client, self.pending_update, OrderPackageType.UPDATE, bet_delay
            )
        if self.pending_replace:
            packages += self._create_packages(
                client, self.pending_replace, OrderPackageType.REPLACE, bet_delay
            )
        if packages:
            logger.info(
                "%s order packages created" % len(packages),
                extra={
                    "order_packages": [o.info for o in packages],
                    "bet_delay": bet_delay,
                },
            )
        return packages

    def _create_packages(
        self, client, orders: list, package_type: OrderPackageType, bet_delay: int
    ) -> list:
        packages = []
        _package_cls = BetfairOrderPackage
        limit = _package_cls.order_limit(package_type)
        # batch based on request data dict
        batched_orders = batch_orders(orders)
        # create packages
        for market_version, mv_batched_orders in batched_orders.items():
            for _orders in mv_batched_orders:
                for chunked_orders in chunks(_orders, limit):
                    order_package = _package_cls(
                        client=client,
                        market_id=self.market_id,
                        orders=chunked_orders,
                        package_type=package_type,
                        bet_delay=bet_delay,
                        market_version=market_version,
                    )
                    packages.append(order_package)
        orders.clear()
        return packages

    @property
    def pending_orders(self) -> bool:
        return any(
            (
                self.pending_place,
                self.pending_cancel,
                self.pending_update,
                self.pending_replace,
            )
        )

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
        for order in self:
            if order.trade.strategy == strategy and order.lookup == lookup:
                if order.status == OrderStatus.VIOLATION:
                    continue

                if order.order_type.ORDER_TYPE == OrderTypes.LIMIT:
                    if order.size_matched:
                        if order.side == "BACK":
                            mb.append((order.average_price_matched, order.size_matched))
                        else:
                            ml.append((order.average_price_matched, order.size_matched))
                    if order.order_type.price and order.size_remaining:
                        if order.side == "BACK":
                            ub.append((order.order_type.price, order.size_remaining))
                        else:
                            ul.append((order.order_type.price, order.size_remaining))
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

    def __getitem__(self, customer_order_ref: str):
        return self._orders[customer_order_ref]

    def __iter__(self) -> Iterable[BaseOrder]:
        return iter(list(self._orders.values()))

    def __len__(self) -> int:
        return len(self._orders)
