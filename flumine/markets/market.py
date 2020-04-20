import datetime
import logging
from betfairlightweight.resources.bettingresources import MarketBook, MarketCatalogue

from .blotter import Blotter
from ..order.orderpackage import BetfairOrderPackage, OrderPackageType
from ..utils import chunks

logger = logging.getLogger(__name__)


class Market:
    def __init__(
        self,
        market_id: str,
        market_book: MarketBook,
        market_catalogue: MarketCatalogue = None,
    ):
        self.market_id = market_id
        self.closed = False
        self.market_book = market_book
        self.market_catalogue = market_catalogue

        self.blotter = Blotter(market_id)
        # pending orders
        self._pending_place = []
        self._pending_cancel = []
        self._pending_update = []
        self._pending_replace = []

    def __call__(self, market_book: MarketBook):
        self.market_book = market_book
        # todo middleware?

    def open_market(self) -> None:
        self.closed = False

    def close_market(self) -> None:
        self.closed = True

    # order
    def place_order(self, order) -> None:
        if order.id not in self.blotter:
            self.blotter[order.id] = order
            # todo log trade?
        else:
            return  # retry attempt so ignore?
        self._pending_place.append(order)

    def cancel_order(self, order) -> None:
        self._pending_cancel.append(order)

    def update_order(self, order) -> None:
        self._pending_update.append(order)

    def replace_order(self, order) -> None:
        self._pending_replace.append(order)

    # process orders
    def process_orders(self, client) -> list:
        packages = []
        if self._pending_place:
            packages += self._create_packages(
                client, self._pending_place, OrderPackageType.PLACE
            )
        if self._pending_cancel:
            packages += self._create_packages(
                client, self._pending_cancel, OrderPackageType.CANCEL
            )
        if self._pending_update:
            packages += self._create_packages(
                client, self._pending_update, OrderPackageType.UPDATE
            )
        if self._pending_replace:
            packages += self._create_packages(
                client, self._pending_replace, OrderPackageType.REPLACE
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
        limit = 100  # todo
        for chunked_orders in chunks(orders, limit):
            order_package = _package_cls(
                client=client,
                market_id=self.market_id,
                orders=chunked_orders,
                package_type=package_type,
            )
            packages.append(order_package)
        orders.clear()
        return packages

    @property
    def seconds_to_start(self):
        return (self.market_start_datetime - datetime.datetime.utcnow()).total_seconds()

    @property
    def market_start_datetime(self):
        if self.market_catalogue:
            return self.market_catalogue.market_start_time
        elif self.market_book:
            return self.market_book.market_definition.market_time
        else:
            return datetime.datetime.utcfromtimestamp(0)
