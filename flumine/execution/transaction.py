import logging
from collections import defaultdict

from ..order.orderpackage import OrderPackageType, BetfairOrderPackage
from ..events import events
from ..exceptions import ControlError

logger = logging.getLogger(__name__)


class Transaction:
    """
    Process place, cancel, update and replace requests.

    Default behaviour is to execute immediately however
    when it is used as a context manager requests can
    be batched, for example:

        with market.transaction as t:
            market.place_order(order)  # executed immediately in separate transaction
            t.place_order(order)  # executed on transaction __exit__

        with market.transaction as t:
            t.place_order(order)
            ..
            t.execute()  # above order executed
            ..
            t.cancel_order(order)
            t.place_order(order)  # both executed on transaction __exit__
    """

    def __init__(self, market):
        self.market = market
        self._pending_place = []  # list of (<Order>, market_version)
        self._pending_cancel = []  # list of <Order>
        self._pending_update = []  # list of <Order>
        self._pending_replace = []  # list of (<Order>, market_version)

    def place_order(
        self, order, market_version: int = None, execute: bool = None
    ) -> bool:
        # validate controls
        validated = self._validate_controls(order, OrderPackageType.PLACE)
        if not validated:
            return False
        # place
        order.place(self.market.market_book.publish_time)
        if order.id not in self.market.blotter:
            self.market.blotter[order.id] = order
            if order.trade.market_notes is None:
                order.trade.update_market_notes(self.market)
            self.market.flumine.log_control(
                events.TradeEvent(order.trade)
            )  # todo dupes?
        else:
            return True  # retry attempt so ignore?
        if execute:  # handles replaceOrder
            self._pending_place.append((order, market_version))
            return True
        else:
            return True

    def cancel_order(self, order, size_reduction: float = None) -> bool:
        # validate controls
        validated = self._validate_controls(order, OrderPackageType.CANCEL)
        if not validated:
            return False
        # cancel
        order.cancel(size_reduction)
        self._pending_cancel.append((order, None))
        return True

    def update_order(self, order, new_persistence_type: str) -> bool:
        # validate controls
        validated = self._validate_controls(order, OrderPackageType.UPDATE)
        if not validated:
            return False
        # update
        order.update(new_persistence_type)
        self._pending_update.append((order, None))
        return True

    def replace_order(
        self, order, new_price: float, market_version: int = None
    ) -> bool:
        # validate controls
        validated = self._validate_controls(order, OrderPackageType.REPLACE)
        if not validated:
            return False
        # replace
        order.replace(new_price)
        self._pending_replace.append((order, market_version))
        return True

    def execute(self) -> int:
        packages = []
        if self._pending_place:
            packages += self._create_order_package(
                self._pending_place,
                OrderPackageType.PLACE,
            )
            self._pending_place.clear()
        if self._pending_cancel:
            packages += self._create_order_package(
                self._pending_cancel,
                OrderPackageType.CANCEL,
            )
            self._pending_cancel.clear()
        if self._pending_update:
            packages += self._create_order_package(
                self._pending_update,
                OrderPackageType.UPDATE,
            )
            self._pending_update.clear()
        if self._pending_replace:
            packages += self._create_order_package(
                self._pending_replace,
                OrderPackageType.REPLACE,
            )
            self._pending_replace.clear()

        if packages:
            for package in packages:
                self.market.flumine.process_order_package(package)
            logger.info(
                "%s order packages executed" % len(packages),
                extra={
                    "market_id": self.market.market_id,
                    "order_packages": [o.info for o in packages],
                },
            )
        return len(packages)

    def _validate_controls(self, order, package_type: OrderPackageType) -> bool:
        # return False on violation
        try:
            for control in self.market.flumine.trading_controls:
                control(order, package_type)
            for control in self.market.flumine.client.trading_controls:
                control(order, package_type)
        except ControlError:
            return False
        else:
            return True

    def _create_order_package(
        self, orders: list, package_type: OrderPackageType
    ) -> list:
        # group orders by marketVersion
        orders_grouped = defaultdict(list)
        for o in orders:
            orders_grouped[o[1]].append(o[0])
        # create packages
        packages = []
        for market_version, package_orders in orders_grouped.items():
            packages.append(
                BetfairOrderPackage(
                    client=self.market.flumine.client,
                    market_id=self.market.market_id,
                    orders=package_orders,
                    package_type=package_type,
                    bet_delay=self.market.market_book.bet_delay,
                    market_version=market_version,
                )
            )
        return packages

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.execute()
