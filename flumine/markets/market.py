from betfairlightweight.resources.bettingresources import MarketBook


class Market:
    def __init__(self, market_id: str, market_book: MarketBook):
        self.market_id = market_id
        self.closed = False
        self.market_book = market_book

    def __call__(self, market_book: MarketBook):
        self.market_book = market_book
        # todo middleware?

    def open_market(self) -> None:
        self.closed = False

    def close_market(self) -> None:
        self.closed = True
