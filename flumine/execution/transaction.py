import logging
from collections import defaultdict

from .. import config
from ..clients import ExchangeType
from ..order.orderpackage import (
    OrderPackageType,
    BetfairOrderPackage,
    BetdaqOrderPackage,
)
from ..events import events
from ..exceptions import ControlError, OrderError
from ..utils import chunks, get_market_notes

logger = logging.getLogger(__name__)


class Transaction:
    """
    Process place, cancel, update and replace requests.

    Transaction per single client/exchange only.

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
    """

    def __init__(
        self,
        market,
        id_: int,
        async_place_orders: bool,
        client,
        customer_strategy_ref=None,
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
        self.customer_strategy_ref = (
            config.customer_strategy_ref or customer_strategy_ref
        )

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
            and self._validate_controls(order, OrderPackageType.PLACE) is False
        ):
            return False
        # place
        order.place(
            self.market.market_book.publish_time,
            market_version,
            self._async_place_orders,
        )
        if self.market.blotter.has_trade(order.trade):
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
            runner_context = order.trade.strategy.get_runner_context(*order.lookup)
            runner_context.place(order.trade.id)
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
            and self._validate_controls(order, OrderPackageType.CANCEL) is False
        ):
            return False
        # cancel
        order.cancel(size_reduction)
        self._pending_cancel.append((order, None))
        self._pending_orders = True
        return True

    def update_order(
        self,
        order,
        # BETFAIR
        new_persistence_type: str = None,
        # BETDAQ
        size_delta: float = 0.0,
        new_price: float = None,
        expected_selection_reset_count: int = None,
        expected_withdrawal_sequence_number: int = None,
        cancel_on_in_running: bool = None,
        cancel_if_selection_reset: bool = None,
        set_to_be_sp_if_unmatched: bool = None,
        force: bool = False,
    ) -> bool:
        if order.client != self._client:
            raise OrderError(
                "update_order: Order client '{0}' does not match transaction client '{1}'".format(
                    order.client, self._client
                )
            )
        if (
            not force
            and self._validate_controls(order, OrderPackageType.UPDATE) is False
        ):
            return False
        # update
        if order.EXCHANGE in [ExchangeType.BETFAIR, ExchangeType.SIMULATED]:
            order.update(new_persistence_type)
        elif order.EXCHANGE == ExchangeType.BETDAQ:
            order.update(
                size_delta,
                new_price,
                expected_selection_reset_count,
                expected_withdrawal_sequence_number,
                cancel_on_in_running,
                cancel_if_selection_reset,
                set_to_be_sp_if_unmatched,
            )
        else:
            raise OrderError(f"update_order: Unknown exchange '{order.EXCHANGE}'")
        self._pending_update.append((order, None))
        self._pending_orders = True
        return True

    def replace_order(
        self, order, new_price: float, market_version: int = None, force: bool = False
    ) -> bool:
        if order.EXCHANGE not in [ExchangeType.BETFAIR, ExchangeType.SIMULATED]:
            raise OrderError(
                f"replace_order: Order EXCHANGE cannot be {order.EXCHANGE}"
            )
        if order.client != self._client:
            raise OrderError(
                "replace_order: Order client '{0}' does not match transaction client '{1}'".format(
                    order.client, self._client
                )
            )
        if (
            not force
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
            for control in self.market.flumine.trading_controls:
                control(order, package_type)
            for control in self._client.trading_controls:
                control(order, package_type)
        except ControlError:
            if package_type != OrderPackageType.PLACE:
                order.executable()  # reset
            return False
        else:
            return True

    def _create_order_package(
        self, orders: list, package_type: OrderPackageType, async_: bool = False
    ) -> list:
        if self._client.EXCHANGE in [ExchangeType.BETFAIR, ExchangeType.SIMULATED]:
            package = BetfairOrderPackage
        elif self._client.EXCHANGE == ExchangeType.BETDAQ:
            package = BetdaqOrderPackage
        else:
            raise OrderError(
                f"Invalid exchange '{self._client.EXCHANGE}' provided to transaction"
            )
        # group orders by marketVersion
        orders_grouped = defaultdict(list)
        for o in orders:
            orders_grouped[o[1]].append(o[0])
        # create packages (chunked by limit)
        limit = package.order_limit(package_type)
        packages = []
        for market_version, package_orders in orders_grouped.items():
            for chunked_orders in chunks(package_orders, limit):
                packages.append(
                    package(
                        client=self._client,
                        market_id=self.market.market_id,
                        orders=chunked_orders,
                        package_type=package_type,
                        bet_delay=self.market.market_book.bet_delay,
                        market_version=market_version,
                        customer_strategy_ref=self.customer_strategy_ref,
                        async_=async_,
                    )
                )
        orders.clear()
        return packages

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._pending_orders:
            self.execute()
