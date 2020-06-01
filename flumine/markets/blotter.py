import logging
from typing import Iterable

from ..utils import chunks, calculate_exposure
from ..order.order import BaseOrder, OrderStatus
from ..order.orderpackage import OrderPackageType, BetfairOrderPackage

logger = logging.getLogger(__name__)

# https://www.betfair.com/aboutUs/Betfair.Charges/#charges6
IMPLIED_COMMISSION_RATE = 0.03


class Blotter:
    def __init__(self, market):
        self.market = market
        self._orders = {}  # {Order.id: Order}
        # pending orders
        self.pending_place = []
        self.pending_cancel = []
        self.pending_update = []
        self.pending_replace = []

    def strategy_orders(self, strategy) -> list:
        """Returns all orders related to a strategy.
        """
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
                market=self.market,
            )
            packages.append(order_package)
        orders.clear()
        return packages

    @property
    def live_orders(self) -> bool:
        for order in self._orders.values():
            if (
                order.status == OrderStatus.EXECUTABLE
                or order.trade.trade_complete is False
            ):
                return True
        return False

    def process_closed_market(self, market_book):
        for order in self:
            for runner in market_book.runners:
                if (order.selection_id, order.handicap) == (
                    runner.selection_id,
                    runner.handicap,
                ):
                    order.runner_status = runner.status

    """ position """

    def selection_exposure(self, strategy, lookup: tuple) -> float:
        """Returns strategy/selection exposure,
        can be positive or negative.
            positive = profit on selection
            negative = exposure on selection
        """
        mb, ml = [], []  # (price, size)
        for order in self:
            if order.trade.strategy == strategy and order.lookup == lookup:
                if order.side == "BACK":
                    mb.append((order.average_price_matched, order.size_matched))
                else:
                    ml.append((order.average_price_matched, order.size_matched))
        return calculate_exposure(mb, ml)

    @property
    def market_id(self):
        return self.market.market_id

    """ getters / setters """

    def has_order(self, customer_order_ref: str) -> bool:
        return customer_order_ref in self._orders

    __contains__ = has_order

    def __setitem__(self, customer_order_ref: str, order) -> None:
        self._orders[customer_order_ref] = order

    def __getitem__(self, customer_order_ref: str):
        return self._orders[customer_order_ref]

    def __iter__(self) -> Iterable[BaseOrder]:
        return iter(self._orders.values())

    def __len__(self) -> int:
        return len(self._orders)
