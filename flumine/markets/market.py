import datetime
import logging
from typing import Optional
from collections import defaultdict
from betfairlightweight.resources.bettingresources import MarketBook, MarketCatalogue

from .. import config
from .blotter import Blotter
from ..execution.transaction import Transaction

logger = logging.getLogger(__name__)


class Market:
    """
    Market data structure to hold latest marketBook,
    marketCatalogue and various properties. Also
    allows order placement through the Transaction
    class.
    """

    def __init__(
        self,
        flumine,
        market_id: str,
        market_book: MarketBook,
        market_catalogue: MarketCatalogue = None,
    ):
        self.flumine = flumine
        self.market_id = market_id
        self.closed = False
        self.date_time_created = datetime.datetime.now(datetime.timezone.utc)
        self.date_time_closed = None
        self.market_book = market_book
        self.market_catalogue = market_catalogue
        self.update_market_catalogue = True
        self.orders_cleared = []
        self.market_cleared = []
        self.context = {"simulated": {}}  # data store (raceCard / scores etc)
        self.blotter = Blotter(market_id)
        self._transaction_id = 0

    def __call__(self, market_book: MarketBook):
        if self.market_book and market_book.version != self.market_book.version:
            self.update_market_catalogue = True
        self.market_book = market_book

    def open_market(self) -> None:
        self.closed = False
        self.orders_cleared = []
        self.market_cleared = []
        logger.info(
            "Market %s opened",
            self.market_id,
            extra=self.info,
        )

    def close_market(self) -> None:
        self.closed = True
        self.date_time_closed = datetime.datetime.now(datetime.timezone.utc)
        logger.info(
            "Market %s closed",
            self.market_id,
            extra=self.info,
        )

    def transaction(
        self, async_place_orders: bool = None, client=None, customer_strategy_ref=None
    ) -> Transaction:
        if async_place_orders is None:
            async_place_orders = config.async_place_orders
        if client is None:
            client = self.flumine.clients.get_default()
        self._transaction_id += 1
        return Transaction(
            self,
            id_=self._transaction_id,
            async_place_orders=async_place_orders,
            client=client,
            customer_strategy_ref=customer_strategy_ref,
        )

    # order
    def place_order(
        self,
        order,
        market_version: int = None,
        execute: bool = True,
        force: bool = False,
        client=None,
        customer_strategy_ref=None,
    ) -> bool:
        if customer_strategy_ref is None and config.customer_strategy_ref is None:
            customer_strategy_ref = str(order.trade.strategy)[:15]
        with self.transaction(
            client=client, customer_strategy_ref=customer_strategy_ref
        ) as t:
            return t.place_order(order, market_version, execute, force)

    def cancel_order(
        self, order, size_reduction: float = None, force: bool = False
    ) -> bool:
        with self.transaction(client=order.client) as t:
            return t.cancel_order(order, size_reduction, force)

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
        with self.transaction(client=order.client) as t:
            return t.update_order(
                order,
                new_persistence_type,
                size_delta,
                new_price,
                expected_selection_reset_count,
                expected_withdrawal_sequence_number,
                cancel_on_in_running,
                cancel_if_selection_reset,
                set_to_be_sp_if_unmatched,
                force,
            )

    def replace_order(
        self, order, new_price: float, market_version: int = None, force: bool = False
    ) -> bool:
        with self.transaction(client=order.client) as t:
            return t.replace_order(order, new_price, market_version, force)

    @property
    def event(self) -> dict:
        event = defaultdict(list)
        market_start_datetime = self.market_start_datetime
        event_type_id = self.event_type_id
        for market in self.flumine.markets.events[self.event_id]:
            if (
                market_start_datetime == market.market_start_datetime
                or event_type_id in ["1", "3"]  # soccer, golf
            ):
                event[market.market_type].append(market)
        return event

    @property
    def event_type_id(self) -> str:
        if self.market_catalogue:
            return self.market_catalogue.event_type.id
        elif self.market_book:
            return self.market_book.market_definition.event_type_id

    @property
    def event_id(self) -> str:
        if self.market_catalogue:
            return self.market_catalogue.event.id
        elif self.market_book:
            if self.market_book.market_definition:
                return self.market_book.market_definition.event_id
            else:
                return ""

    @property
    def market_type(self) -> str:
        if self.market_catalogue and self.market_catalogue.description:
            return self.market_catalogue.description.market_type
        elif self.market_book:
            return self.market_book.market_definition.market_type

    @property
    def seconds_to_start(self) -> float:
        return (
            self.market_start_datetime
            - datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        ).total_seconds()

    @property
    def elapsed_seconds_closed(self) -> Optional[float]:
        if self.closed and self.date_time_closed:
            return (
                datetime.datetime.now(datetime.timezone.utc) - self.date_time_closed
            ).total_seconds()

    @property
    def market_start_datetime(self):
        if self.market_book:
            return self.market_book.market_definition.market_time
        elif self.market_catalogue:
            return self.market_catalogue.market_start_time
        else:
            return datetime.datetime.fromtimestamp(0)

    @property
    def market_start_hour_minute(self) -> Optional[str]:
        msd = self.market_start_datetime
        if msd:
            return "{0:02d}{1:02d}".format(msd.hour, msd.minute)

    @property
    def event_name(self) -> Optional[str]:
        if self.market_catalogue:
            return self.market_catalogue.event.name
        elif self.market_book:
            return self.market_book.market_definition.event_name

    @property
    def country_code(self) -> Optional[str]:
        if self.market_catalogue:
            return self.market_catalogue.event.country_code
        elif self.market_book:
            return self.market_book.market_definition.country_code

    @property
    def venue(self) -> Optional[str]:
        if self.market_catalogue:
            return self.market_catalogue.event.venue
        elif self.market_book:
            return self.market_book.market_definition.venue

    @property
    def race_type(self) -> Optional[str]:
        if self.market_catalogue and self.market_catalogue.description:
            return self.market_catalogue.description.race_type
        elif self.market_book:
            return self.market_book.market_definition.race_type

    @property
    def status(self) -> Optional[str]:
        if self.market_book:
            return self.market_book.status

    def cleared(self, client) -> dict:
        orders = self.blotter.client_orders(client, matched_only=True)
        profit = round(sum([order.profit for order in orders]), 2)
        return {
            "marketId": self.market_id,
            "eventId": self.event_id,
            "eventTypeId": self.event_type_id,
            "customerStrategyRef": config.customer_strategy_ref,
            "lastMatchedDate": None,
            "placedDate": None,
            "settledDate": None,
            "betCount": len(orders),
            "betOutcome": "WON" if profit >= 0 else "LOST",
            "commission": round(max(profit * client.commission_base, 0), 2),
            "profit": profit,
        }

    @property
    def info(self) -> dict:
        return {
            "market_id": self.market_id,
            "event_id": self.event_id,
            "event_type_id": self.event_type_id,
            "event_name": self.event_name,
            "market_type": self.market_type,
            "market_start_datetime": str(self.market_start_datetime),
            "country_code": self.country_code,
            "venue": self.venue,
            "race_type": self.race_type,
            "orders_cleared": self.orders_cleared,
            "market_cleared": self.market_cleared,
            "closed": self.closed,
        }
