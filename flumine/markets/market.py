import datetime
import logging
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
        self.market_book = market_book
        self.market_catalogue = market_catalogue
        self.context = {"simulated": {}}  # data store (raceCard / scores etc)
        self.blotter = Blotter(self)

    def __call__(self, market_book: MarketBook):
        self.market_book = market_book

    def open_market(self) -> None:
        self.closed = False

    def close_market(self) -> None:
        self.closed = True

    # order
    def place_order(self, order, execute: bool = True) -> None:
        order.place()
        if order.id not in self.blotter:
            self.blotter[order.id] = order
            self.flumine.log_control(events.TradeEvent(order.trade))  # todo dupes?
            self.flumine.log_control(events.OrderEvent(order))
        else:
            return  # retry attempt so ignore?
        if execute:  # handles replaceOrder
            self.blotter.pending_place.append(order)

    def cancel_order(self, order, size_reduction: float = None) -> None:
        order.cancel(size_reduction)
        self.blotter.pending_cancel.append(order)

    def update_order(self, order, new_persistence_type: str) -> None:
        order.update(new_persistence_type)
        self.blotter.pending_update.append(order)

    def replace_order(self, order, new_price: float) -> None:
        order.replace(new_price)
        self.blotter.pending_replace.append(order)

    @property
    def event_type_id(self) -> str:
        if self.market_book:
            return self.market_book.market_definition.event_type_id

    @property
    def event_id(self) -> str:
        if self.market_book:
            return self.market_book.market_definition.event_id

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
