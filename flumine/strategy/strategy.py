from betfairlightweight.resources import MarketBook, RaceCard, CurrentOrders


class Strategies:
    def __init__(self):
        self._strategies = []

    def __call__(self, strategy):
        self._strategies.append(strategy)
        strategy.start()

    def __iter__(self):
        return iter(self._strategies)

    def __len__(self):
        return len(self._strategies)


class BaseStrategy:
    def __init__(
        self,
        market_filter: dict,
        market_data_filter: dict = None,
        streaming_timeout: float = None,
        raw_data: bool = False,
    ):
        self.market_filter = market_filter
        self.market_data_filter = market_data_filter
        self.streaming_timeout = streaming_timeout
        self.raw_data = raw_data

        self.streams = []  # list of streams strategy is subscribed

    def check_market(self, market_book: MarketBook) -> bool:
        if market_book.streaming_unique_id not in self.stream_ids:
            return False  # strategy not subscribed to market stream
        elif self.check_market_book(market_book):
            return True
        else:
            return False

    def start(self) -> None:
        # subscribe to streams
        return

    def check_market_book(self, market_book: MarketBook) -> bool:
        # process_market_book only executed if this returns True
        return False

    def process_market_book(self, market_book: MarketBook) -> None:
        # process marketBook; place/cancel/replace orders
        return

    def process_raw_data(self, publish_time: int, datum: dict) -> None:
        return

    def process_race_card(self, race_card: RaceCard) -> None:
        # process raceCard object
        return

    def process_orders(self, orders: CurrentOrders) -> None:
        # process currentOrders object
        return

    @property
    def stream_ids(self) -> list:
        return [stream.stream_id for stream in self.streams]
