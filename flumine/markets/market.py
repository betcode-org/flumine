import datetime
import logging
from typing import Optional
from collections import defaultdict
from pathlib import Path
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
        self.date_time_created = datetime.datetime.utcnow()
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
        self.date_time_closed = datetime.datetime.utcnow()
        logger.info(
            "Market %s closed",
            self.market_id,
            extra=self.info,
        )

    def matches_streaming_market_filter(self, market_filter: dict) -> bool:
        """
        Returns True if this market matches the provided streaming market filter.
        In other words, if the market filter would end up subscribing to this market.

        For a simulation market filter in the form of {"markets": [<file 1>, <file 2>, ...]},
        file names should comprise of a market id followed by optional extensions, like so:
        <market_id>[.<extensions>] e.g. "1.12345678", "1.12345678.json" or "1.12345678.tar.gz".
        """
        market_files = market_filter.get("markets")
        if market_files:  # Simulation
            return any(
                self.market_id.endswith(p.suffixes[0])
                for p in map(Path, market_files)
                if p.suffix
            )
        else:  # Live
            market_metadata = {  # Expected filter values for this market
                "marketIds": self.market_id,
                "bspMarket": self.market_book.market_definition.bsp_market,
                "bettingTypes": self.market_book.market_definition.betting_type,
                "eventTypeIds": self.event_type_id,
                "eventIds": self.event_id,
                "turnInPlayEnabled": self.market_book.market_definition.turn_in_play_enabled,
                "marketTypes": self.market_type,
                "venues": self.venue,
                "countryCodes": self.country_code,
                "raceTypes": self.race_type,
            }
            try:
                for field_name, filter_value in market_filter.items():
                    if isinstance(filter_value, bool):
                        if market_metadata[field_name] is not filter_value:
                            return False
                    elif isinstance(filter_value, list):
                        if market_metadata[field_name] not in filter_value:
                            return False
                    else:
                        return False  # Invalid streaming market filter value
            except KeyError:
                return False  # Market filter contains an unsupported field
            return True  # All checks passed

    def transaction(self, async_place_orders: bool = None, client=None) -> Transaction:
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
        )

    # order
    def place_order(
        self,
        order,
        market_version: int = None,
        execute: bool = True,
        force: bool = False,
        client=None,
    ) -> bool:
        with self.transaction(client=client) as t:
            return t.place_order(order, market_version, execute, force)

    def cancel_order(
        self, order, size_reduction: float = None, force: bool = False
    ) -> bool:
        with self.transaction(client=order.client) as t:
            return t.cancel_order(order, size_reduction, force)

    def update_order(
        self, order, new_persistence_type: str, force: bool = False
    ) -> bool:
        with self.transaction(client=order.client) as t:
            return t.update_order(order, new_persistence_type, force)

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
                or event_type_id == "1"
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
            return self.market_book.market_definition.event_id

    @property
    def market_type(self) -> str:
        if self.market_catalogue:
            return self.market_catalogue.description.market_type
        elif self.market_book:
            return self.market_book.market_definition.market_type

    @property
    def seconds_to_start(self) -> float:
        return (self.market_start_datetime - datetime.datetime.utcnow()).total_seconds()

    @property
    def elapsed_seconds_closed(self) -> Optional[float]:
        if self.closed and self.date_time_closed:
            return (datetime.datetime.utcnow() - self.date_time_closed).total_seconds()

    @property
    def market_start_datetime(self):
        if self.market_book:
            return self.market_book.market_definition.market_time
        elif self.market_catalogue:
            return self.market_catalogue.market_start_time
        else:
            return datetime.datetime.utcfromtimestamp(0)

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
        if self.market_catalogue:
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
