import datetime
from betfairlightweight.resources.bettingresources import MarketBook, MarketCatalogue


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

    def __call__(self, market_book: MarketBook):
        self.market_book = market_book
        # todo middleware?

    def open_market(self) -> None:
        self.closed = False

    def close_market(self) -> None:
        self.closed = True

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
