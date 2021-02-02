import logging
from ..order.orderpackage import OrderPackageType, BetfairOrderPackage

logger = logging.getLogger(__name__)


class Transaction:
    """
    Process place, cancel, update and replace requests.

    Default behaviour is to execute immediately however
    when it is used as a context manager requests can
    be batched, for example:

        with market.transaction:
            market.place_order(order)  # execute on transaction __exit__

        with market.transaction as t:
            market.place_order(order)
            ..
            t.place_order(order)
            ..
            t.execute()  # above 2 orders executed
            ..
            t.cancel_order(order)
            t.place_order(order)  # executed on transaction __exit__
    """

    def __init__(self, market):
        self.market = market
        self.open = False
        self._pending_place = []  # list of (<Order>, market_version)
        self._pending_cancel = []  # list of <Order>
        self._pending_update = []  # list of <Order>
        self._pending_replace = []  # list of (<Order>, market_version)

    def place_order(self, order, market_version: int) -> None:
        if self.open:  # open transaction
            self._pending_place.append((order, market_version))
        else:
            package = self._create_order_package(
                self._pending_place,
                OrderPackageType.PLACE,  # todo market_version
            )
            self.market.flumine.process_order_package(package)

    def cancel_order(self, order) -> None:
        pass

    def update_order(self, order) -> None:
        pass

    def replace_order(self, order, market_version: int) -> None:
        pass

    def execute(self) -> int:
        packages = []
        if self._pending_place:
            packages.append(
                self._create_order_package(
                    self._pending_place,
                    OrderPackageType.PLACE,  # todo market_version
                )
            )
            self._pending_place.clear()
        if self._pending_cancel:
            # todo
            self._pending_cancel.clear()
        if self._pending_update:
            # todo
            self._pending_update.clear()
        if self._pending_replace:
            # todo
            self._pending_replace.clear()

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

    def _create_order_package(
        self, orders: list, package_type: OrderPackageType, market_version: int = None
    ) -> BetfairOrderPackage:
        return BetfairOrderPackage(
            client=self.market.flumine.client,
            market_id=self.market.market_id,
            orders=orders,
            package_type=package_type,
            bet_delay=self.market.market_book.bet_delay,
            market_version=market_version,
        )

    def __enter__(self):
        self.open = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.execute()
        self.open = False
