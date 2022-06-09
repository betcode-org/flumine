import logging
from collections import defaultdict
from typing import Optional

from ..order.orderpackage import OrderPackageType, BetfairOrderPackage
from ..events import events
from ..exceptions import ControlError, OrderError
from ..utils import chunks, get_market_notes

logger = logging.getLogger(__name__)


class Transaction:
    """
    Process place, cancel, update and replace requests.

    Default behaviour is to execute immediately however
    when it is used as a context manager requests can
    be batched, for example:

        with market.transaction() as t:
            market.place_order(order)  # executed immediately in separate transaction
            t.place_order(order)  # executed on transaction __exit__

        with market.transaction() as t:
            t.place_order(order)
            ..
            t.execute()  # above order executed
            ..
            t.cancel_order(order)
            t.place_order(order)  # both executed on transaction __exit__

    When atomic==True, orders within a transaction will
    only be placed if the all pass validation.
    For example, supposed we have:

        with market.transaction(atomic=True) as t:
            t.place_order(order1) # validation passes
            t.place_order(order2) # validation does not pass and raises a ControlError

    Neither order1 nor order2 will be executed, as order2 failed validation.

    """

    def __init__(
        self,
        market,
        id_: int,
        async_place_orders: bool,
        client,
        atomic: Optional[bool] = False,
    ):
        self.market = market
        self._client = client
        self._id = id_  # unique per market only
        self._async_place_orders = async_place_orders
        self._pending_orders = False
        self._pending_place = []  # list of (<Order>, market_version)
        self._pending_cancel = []  # list of (<Order>, None)
        self._pending_update = []  # list of (<Order>, None)
        self._pending_replace = []  # list of (<Order>, market_version)
        self.atomic = atomic

    def place_order(
        self,
        order,
        market_version: int = None,
        execute: bool = True,
        force: bool = False,
    ) -> bool:
        order.update_client(self._client)
        if (
            execute
            and not force
            and not self.atomic
            and self._validate_controls(order, OrderPackageType.PLACE) is False
        ):
            return False
        # place
        order.place(
            self.market.market_book.publish_time,
            market_version,
            self._async_place_orders,
        )
        if self.market.blotter.has_trade(order.trade.id):
            new_trade = False
        else:
            new_trade = True
        if order.id not in self.market.blotter:
            self.market.blotter[order.id] = order
            # update market_notes
            market_notes = get_market_notes(self.market, order.selection_id)
            order.market_notes = market_notes
            if order.trade.market_notes is None:
                order.trade.market_notes = market_notes
        else:
            raise OrderError("Order %s has already been placed" % order.id)
        if new_trade:
            self.market.flumine.log_control(events.TradeEvent(order.trade))
        if execute:  # handles replaceOrder
            self._pending_place.append((order, market_version))
            self._pending_orders = True
        return True

    def cancel_order(
        self, order, size_reduction: float = None, force: bool = False
    ) -> bool:
        if order.client != self._client:
            raise OrderError(
                "cancel_order: Order client '{0}' does not match transaction client '{1}'".format(
                    order.client, self._client
                )
            )
        if (
            not force
            and not self.atomic
            and self._validate_controls(order, OrderPackageType.CANCEL) is False
        ):
            return False
        # cancel
        order.cancel(size_reduction)
        self._pending_cancel.append((order, None))
        self._pending_orders = True
        return True

    def update_order(
        self, order, new_persistence_type: str, force: bool = False
    ) -> bool:
        if order.client != self._client:
            raise OrderError(
                "update_order: Order client '{0}' does not match transaction client '{1}'".format(
                    order.client, self._client
                )
            )
        if (
            not force
            and not self.atomic
            and self._validate_controls(order, OrderPackageType.UPDATE) is False
        ):
            return False
        # update
        order.update(new_persistence_type)
        self._pending_update.append((order, None))
        self._pending_orders = True
        return True

    def replace_order(
        self, order, new_price: float, market_version: int = None, force: bool = False
    ) -> bool:
        if order.client != self._client:
            raise OrderError(
                "replace_order: Order client '{0}' does not match transaction client '{1}'".format(
                    order.client, self._client
                )
            )
        if (
            not force
            and not self.atomic
            and self._validate_controls(order, OrderPackageType.REPLACE) is False
        ):
            return False
        # replace
        order.replace(new_price)
        self._pending_replace.append((order, market_version))
        self._pending_orders = True
        return True

    def execute(self) -> int:
        packages = []
        if self._pending_place:
            for order, market_version in self._pending_place:
                runner_context = order.trade.strategy.get_runner_context(*order.lookup)
                runner_context.place(order.trade.id)
            packages += self._create_order_package(
                self._pending_place,
                OrderPackageType.PLACE,
                async_=self._async_place_orders,
            )
        if self._pending_cancel:
            packages += self._create_order_package(
                self._pending_cancel,
                OrderPackageType.CANCEL,
            )
        if self._pending_update:
            packages += self._create_order_package(
                self._pending_update,
                OrderPackageType.UPDATE,
            )
        if self._pending_replace:
            packages += self._create_order_package(
                self._pending_replace,
                OrderPackageType.REPLACE,
            )
        if packages:
            for package in packages:
                self.market.flumine.process_order_package(package)
            if logger.isEnabledFor(logging.INFO):
                logger.info(
                    "%s order packages executed in transaction" % len(packages),
                    extra={
                        "market_id": self.market.market_id,
                        "order_packages": [o.info for o in packages],
                        "transaction_id": self._id,
                        "client_username": self._client.username,
                    },
                )
            self._pending_orders = False
        return len(packages)

    def _validate_controls(self, order, package_type: OrderPackageType) -> bool:
        # return False on violation
        try:
            self._do_validate_controls(order, package_type)
        except ControlError:
            return False
        else:
            return True

    def _do_validate_controls(self, order, package_type):
        for control in self.market.flumine.trading_controls:
            control(order, package_type)
        for control in self._client.trading_controls:
            control(order, package_type)

    def _create_order_package(
        self, orders: list, package_type: OrderPackageType, async_: bool = False
    ) -> list:
        # group orders by marketVersion
        orders_grouped = defaultdict(list)
        for o in orders:
            orders_grouped[o[1]].append(o[0])
        # create packages (chunked by limit)
        limit = BetfairOrderPackage.order_limit(package_type)
        packages = []
        for market_version, package_orders in orders_grouped.items():
            for chunked_orders in chunks(package_orders, limit):
                packages.append(
                    BetfairOrderPackage(
                        client=self._client,
                        market_id=self.market.market_id,
                        orders=chunked_orders,
                        package_type=package_type,
                        bet_delay=self.market.market_book.bet_delay,
                        market_version=market_version,
                        async_=async_,
                    )
                )
        orders.clear()
        return packages

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):

        if self._pending_orders:

            if self.atomic:
                try:
                    for order in self._pending_place:
                        self._do_validate_controls(order, OrderPackageType.PLACE)
                    for order in self._pending_cancel:
                        self._do_validate_controls(order, OrderPackageType.CANCEL)
                    for order in self._pending_update:
                        self._do_validate_controls(order, OrderPackageType.UPDATE)
                    for order in self._pending_replace:
                        self._do_validate_controls(order, OrderPackageType.REPLACE)
                except ControlError as e:
                    if logger.isEnabledFor(logging.INFO):
                        extra = {
                            "market_id": self.market.market_id,
                            "transaction_id": self._id,
                            "client_username": self._client.username,
                        }
                        if self._pending_place:
                            extra["pending_place"] = self._pending_place
                        if self._pending_update:
                            extra["pending_update"] = self._pending_update
                        if self._pending_cancel:
                            extra["pending_cancel"] = self._pending_cancel
                        if self._pending_replace:
                            extra["pending_replace"] = self._pending_replace
                        logger.info(
                            "Failed to execute transaction. Validation failed: %s"
                            % str(e),
                            extra=extra,
                        )
                    self._clear()
                    raise
            self.execute()

    def _clear(self):
        self._pending_place.clear()
        self._pending_update.clear()
        self._pending_replace.clear()
        self._pending_cancel.clear()
        self._pending_orders = False
