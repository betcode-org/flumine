import logging
from typing import Iterable

from ..order.ordertype import OrderTypes
from ..utils import chunks, calculate_matched_exposure, calculate_unmatched_exposure
from ..order.order import BaseOrder
from ..order.orderpackage import OrderPackageType, BetfairOrderPackage

logger = logging.getLogger(__name__)

# https://www.betfair.com/aboutUs/Betfair.Charges/#charges6
IMPLIED_COMMISSION_RATE = 0.03


class Blotter:
    def __init__(self, market, market_id: str):
        self.market = market  # weakref
        self.market_id = market_id
        self._orders = {}  # {Order.id: Order}
        self._live_orders = []  # cached list of live orders
        # pending orders
        self.pending_place = []
        self.pending_cancel = []
        self.pending_update = []
        self.pending_replace = []

    def strategy_orders(self, strategy) -> list:
        """Returns all orders related to a strategy."""
        return [order for order in self if order.trade.strategy == strategy]

    def process_orders(self, client) -> list:
        packages = []
        if self.pending_place:
            packages += self._create_packages(
                client, self.pending_place, OrderPackageType.PLACE
            )
        if self.pending_cancel:
            packages += self._create_packages(
                client, self.pending_cancel, OrderPackageType.CANCEL
            )
        if self.pending_update:
            packages += self._create_packages(
                client, self.pending_update, OrderPackageType.UPDATE
            )
        if self.pending_replace:
            packages += self._create_packages(
                client, self.pending_replace, OrderPackageType.REPLACE
            )
        if packages:
            logger.info(
                "%s order packages created" % len(packages),
                extra={"order_packages": [o.info for o in packages]},
            )
        return packages

    def _create_packages(
        self, client, orders: list, package_type: OrderPackageType
    ) -> list:
        packages = []
        _package_cls = BetfairOrderPackage
        limit = _package_cls.order_limit(package_type)
        for chunked_orders in chunks(orders, limit):
            order_package = _package_cls(
                client=client,
                market_id=self.market_id,
                orders=chunked_orders,
                package_type=package_type,
                market=self.market(),
            )
            packages.append(order_package)
        orders.clear()
        return packages

    @property
    def live_orders(self):
        return iter(self._live_orders)

    @property
    def has_live_orders(self):
        return bool(self._live_orders)

    def process_closed_market(self, market_book):
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
        """Returns strategy/selection exposure, which is the worse-case profit/loss arising
        from the selection either winning or losing. Can be positive or negative.

        For matched sizes, the profit/exposure is always considered.
        For unmatched sizes, we only consider potential losses if the unmatched size is matched.

            positive = profit on selection
            negative = exposure on selection
        """
        mb, ml = [], []  # matched bets, (price, size)
        ub, ul = [], []  # unmatched bets, (price, size)
        moc_win_liability = 0.0
        moc_lose_liability = 0.0
        for order in self:
            if order.trade.strategy == strategy and order.lookup == lookup:
                if order.order_type.ORDER_TYPE == OrderTypes.LIMIT:
                    if order.size_matched:
                        if order.side == "BACK":
                            mb.append((order.average_price_matched, order.size_matched))
                        else:
                            ml.append((order.average_price_matched, order.size_matched))
                    size_remaining = order.size_remaining
                    if size_remaining:
                        if order.side == "BACK":
                            ub.append((order.order_type.price, order.size_remaining))
                        else:
                            ul.append((order.order_type.price, order.size_remaining))
                elif order.order_type.ORDER_TYPE in (
                    OrderTypes.MARKET_ON_CLOSE,
                    OrderTypes.MARKET_ON_CLOSE,
                ):
                    if order.side == "BACK":
                        moc_lose_liability -= order.order_type.liability
                    else:
                        moc_win_liability -= order.order_type.liability
                else:
                    raise ValueError("Unexpected order type: %s" % order.order_type)

        matched_exposure = calculate_matched_exposure(mb, ml)
        unmatched_exposure = calculate_unmatched_exposure(ub, ul)
        return (
            matched_exposure[0] + unmatched_exposure[0] + moc_win_liability,
            matched_exposure[1] + unmatched_exposure[1] + moc_lose_liability,
        )

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
