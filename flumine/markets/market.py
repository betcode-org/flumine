import datetime
import logging
from betfairlightweight.resources.bettingresources import MarketBook, MarketCatalogue

from .blotter import Blotter
from .middleware import SimulatedMiddleware
from .. import config

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
        self._simulated_middleware = SimulatedMiddleware()
        self._middleware = [self._simulated_middleware]
        self.blotter = Blotter(self)

    def __call__(self, market_book: MarketBook):
        self.market_book = market_book
        # process middleware
        for middleware in self._middleware:
            middleware(self.market_catalogue, self.market_book)  # todo error handling?
        # process simulated orders
        for order in self.blotter:
            if order.simulated:
                runner_analytics = self._simulated_middleware.runners.get(
                    (order.selection_id, order.handicap)
                )
                order.simulated(self.market_book, runner_analytics)

    def open_market(self) -> None:
        self.closed = False

    def close_market(self) -> None:
        self.closed = True

    # order
    def place_order(self, order, execute: bool = True) -> None:
        order.place()
        if order.id not in self.blotter:
            self.blotter[order.id] = order
            # todo log trade?
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
