from betfairlightweight.resources import MarketBook, RaceCard, CurrentOrders


class Strategies:
    def __init__(self):
        self.strategies = []

    def __call__(self, strategy):
        self.strategies.append(strategy)
        strategy.start()

    def __iter__(self):
        return iter(self.strategies)

    def __len__(self):
        return len(self.strategies)


class BaseStrategy:
    def __init__(self, market_filter: dict, market_data_filter: dict = None):
        self.market_filter = market_filter
        self.market_data_filter = market_data_filter

    def start(self):
        # subscribe to streams
        return

    def check_market_book(self, market_book: MarketBook) -> bool:
        # process_market_book only executed if this returns True
        raise NotImplementedError

    def process_market_book(self, market_book: MarketBook) -> None:
        # process marketBook; place/cancel/replace orders
        raise NotImplementedError

    def process_race_card(self, race_card: RaceCard) -> None:
        # process raceCard object
        return

    def process_orders(self, orders: CurrentOrders) -> None:
        # process currentOrders object
        return
