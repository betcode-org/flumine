import datetime
import logging
from typing import Optional
from collections import defaultdict
from betfairlightweight.resources.bettingresources import MarketBook, MarketCatalogue

from .blotter import Blotter
from ..events import events

logger = logging.getLogger(__name__)


class Market:
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
        self.date_time_closed = None
        self.market_book = market_book
        self.market_catalogue = market_catalogue
        self.update_market_catalogue = True
        self.context = {"simulated": {}}  # data store (raceCard / scores etc)
        self.blotter = Blotter(market_id)

    def __call__(self, market_book: MarketBook):
        if market_book.version != self.market_book.version:
            self.update_market_catalogue = True
        self.market_book = market_book

    def open_market(self) -> None:
        self.closed = False
        logger.info(
            "Market {0} opened".format(self.market_id),
            extra=self.info,
        )

    def close_market(self) -> None:
        self.closed = True
        self.date_time_closed = datetime.datetime.utcnow()
        logger.info(
            "Market {0} closed".format(self.market_id),
            extra=self.info,
        )

    # order
    def place_order(
        self,
        order,
        batch: bool = True,
        market_version: int = None,
        execute: bool = True,
    ) -> None:
        order.place(self.market_book.publish_time)
        if order.id not in self.blotter:
            self.blotter[order.id] = order
            if order.trade.market_notes is None:
                order.trade.update_market_notes(self)
            self.flumine.log_control(events.TradeEvent(order.trade))  # todo dupes?
        else:
            return  # retry attempt so ignore?
        if execute:  # handles replaceOrder
            self.blotter.pending_place.append(
                (order, {"batch": batch, "market_version": market_version})
            )

    def cancel_order(
        self, order, size_reduction: float = None, batch: bool = True
    ) -> None:
        order.cancel(size_reduction)
        self.blotter.pending_cancel.append(
            (order, {"size_reduction": size_reduction, "batch": batch})
        )

    def update_order(
        self, order, new_persistence_type: str, batch: bool = True
    ) -> None:
        order.update(new_persistence_type)
        self.blotter.pending_update.append(
            (order, {"new_persistence_type": new_persistence_type, "batch": batch})
        )

    def replace_order(
        self, order, new_price: float, batch: bool = True, market_version: int = None
    ) -> None:
        order.replace(new_price)
        self.blotter.pending_replace.append(
            (
                order,
                {
                    "new_price": new_price,
                    "batch": batch,
                    "market_version": market_version,
                },
            )
        )

    @property
    def event(self) -> dict:
        event = defaultdict(list)
        for market in self.flumine.markets:
            if market.event_id == self.event_id:
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
        if self.market_catalogue:
            return self.market_catalogue.market_start_time
        elif self.market_book:
            return self.market_book.market_definition.market_time
        else:
            return datetime.datetime.utcfromtimestamp(0)

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
        }
