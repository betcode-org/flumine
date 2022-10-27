import logging
from typing import Type, Iterator, Union, List
from betfairlightweight import filters
from betfairlightweight.resources import MarketBook, Race, CricketMatch

from .runnercontext import RunnerContext
from ..markets.market import Market
from ..streams.marketstream import BaseStream, MarketStream
from ..utils import create_cheap_hash, STRATEGY_NAME_HASH_LENGTH

logger = logging.getLogger(__name__)

DEFAULT_MARKET_DATA_FILTER = filters.streaming_market_data_filter(
    fields=[
        "EX_ALL_OFFERS",
        "EX_TRADED",
        "EX_TRADED_VOL",
        "EX_LTP",
        "EX_MARKET_DEF",
        "SP_TRADED",
        "SP_PROJECTED",
    ]
)


class BaseStrategy:

    """
    Strategy object to process MarketBook data
    from streams, order placement and handling
    logic to be added where required. Only
    MarketBooks from provided filter and data
    filter are processed.
    Runner context available to store current
    live trades.
    """

    def __init__(
        self,
        market_filter: Union[dict, list],
        market_data_filter: dict = None,
        sports_data_filter: List[
            str
        ] = None,  # 'raceSubscription', 'cricketSubscription'
        streaming_timeout: float = None,
        conflate_ms: int = None,
        stream_class: Type[BaseStream] = MarketStream,
        name: str = None,
        context: dict = None,
        max_selection_exposure: float = 100,
        max_order_exposure: float = 10,
        max_trade_count: int = 1e6,
        max_live_trade_count: int = 1,
        multi_order_trades: bool = False,
    ):
        """
        :param market_filter: Streaming market filter dict or list of market filters
        :param market_data_filter: Streaming market data filter
        :param sports_data_filter: Streaming sports data filter (e.g. ["raceSubscription"])
        :param streaming_timeout: Streaming timeout in seconds, will call snap() on cache
        :param conflate_ms: Streaming conflation
        :param stream_class: Can be Market or Data (raw)
        :param name: Strategy name (will default to class name)
        :param context: Dictionary holding additional user specific vars
        :param max_selection_exposure: Max exposure per selection
        :param max_order_exposure: Max exposure per order
        :param max_trade_count: max total number of trades per runner
        :param max_live_trade_count: max live (with executable orders) trades per runner
        :param multi_order_trades: allow multiple live orders per trade
        """
        self.market_filter = market_filter
        self.market_data_filter = market_data_filter or DEFAULT_MARKET_DATA_FILTER
        self.sports_data_filter = sports_data_filter or []
        self.streaming_timeout = streaming_timeout
        self.conflate_ms = conflate_ms
        self.stream_class = stream_class
        self._name = name
        self.context = context or {}
        self.max_selection_exposure = max_selection_exposure
        self.max_order_exposure = max_order_exposure
        self.clients = None
        self.max_trade_count = max_trade_count
        self.max_live_trade_count = max_live_trade_count
        self.multi_order_trades = multi_order_trades

        self._invested = {}  # {(marketId, selectionId, handicap): RunnerContext}
        self.streams = []  # list of streams strategy is subscribed
        self.historic_stream_ids = []
        # cache
        self.name_hash = create_cheap_hash(self.name, STRATEGY_NAME_HASH_LENGTH)

    def add(self) -> None:
        # called when strategy is added to framework
        return

    def start(self) -> None:
        # called when flumine starts but before streams start
        # e.g. subscribe to extra streams
        return

    def check_market(self, market: Market, market_book: MarketBook) -> bool:
        if market_book.streaming_unique_id not in self.stream_ids:
            return False  # strategy not subscribed to market stream
        elif self.check_market_book(market, market_book):
            return True
        else:
            return False

    def check_market_book(self, market: Market, market_book: MarketBook) -> bool:
        # process_market_book only executed if this returns True
        return False

    def process_market_book(self, market: Market, market_book: MarketBook) -> None:
        # process marketBook; place/cancel/replace orders
        return

    def check_sports(
        self, market: Market, sports_data: Union[Race, CricketMatch]
    ) -> bool:
        if sports_data.streaming_unique_id not in self.stream_ids:
            return False  # strategy not subscribed to sports stream
        elif self.check_sports_data(market, sports_data):
            return True
        else:
            return False

    def check_sports_data(
        self, market: Market, sports_data: Union[Race, CricketMatch]
    ) -> bool:
        # process_sports_data only executed if this returns True
        return False

    def process_sports_data(
        self, market: Market, sports_data: Union[Race, CricketMatch]
    ) -> None:
        # process sports data
        return

    def process_raw_data(self, clk: str, publish_time: int, datum: dict) -> None:
        return

    def process_orders(self, market: Market, orders: list) -> None:
        # process list of Order objects for strategy and Market
        return

    def process_closed_market(self, market: Market, market_book: MarketBook) -> None:
        # process marketBook after closure
        return

    def finish(self, flumine) -> None:
        # called before flumine ends
        return

    def remove_market(self, market_id: str) -> None:
        to_remove = []
        for invested in self._invested:
            if invested[0] == market_id:
                to_remove.append(invested)
        for i in to_remove:
            del self._invested[i]

    def validate_order(self, runner_context: RunnerContext, order) -> bool:
        # allow multiple orders per trade
        if self.multi_order_trades:
            if order.trade.id in runner_context.live_trades:
                return True
        # validate context
        reset_elapsed_seconds = runner_context.reset_elapsed_seconds
        if reset_elapsed_seconds and reset_elapsed_seconds < order.trade.reset_seconds:
            order.violation_msg = (
                "strategy.validate_order failed: reset_elapsed_seconds (%s) < reset_seconds (%s)"
                % (
                    reset_elapsed_seconds,
                    order.trade.reset_seconds,
                )
            )
            return False

        placed_elapsed_seconds = runner_context.placed_elapsed_seconds
        if (
            placed_elapsed_seconds
            and placed_elapsed_seconds < order.trade.place_reset_seconds
        ):
            order.violation_msg = (
                "strategy.validate_order failed: placed_elapsed_seconds (%s) < place_reset_seconds (%s)"
                % (
                    placed_elapsed_seconds,
                    order.trade.place_reset_seconds,
                )
            )
            return False

        if runner_context.trade_count >= self.max_trade_count:
            order.violation_msg = (
                "strategy.validate_order failed: trade_count (%s) >= max_trade_count (%s)"
                % (runner_context.trade_count, self.max_trade_count)
            )
            return False
        elif runner_context.live_trade_count >= self.max_live_trade_count:
            order.violation_msg = (
                "strategy.validate_order failed: live_trade_count (%s) >= max_live_trade_count (%s)"
                % (runner_context.live_trade_count, self.max_live_trade_count)
            )
            return False

        return True

    def has_executable_orders(
        self, market_id: str, selection_id: int, handicap: float = 0
    ) -> bool:
        runner_context = self.get_runner_context(market_id, selection_id, handicap)
        return runner_context.executable_orders

    def get_runner_context(
        self, market_id: str, selection_id: int, handicap: float = 0
    ) -> RunnerContext:
        try:
            return self._invested[(market_id, selection_id, handicap)]
        except KeyError:
            self._invested[
                (market_id, selection_id, handicap)
            ] = runner_context = RunnerContext(selection_id)
            return runner_context

    @property
    def stream_ids(self) -> list:
        if self.historic_stream_ids:
            return self.historic_stream_ids
        else:
            return [stream.stream_id for stream in self.streams]

    @property
    def info(self) -> dict:
        return {
            "name": self.name,
            "market_filter": self.market_filter,
            "market_data_filter": self.market_data_filter,
            "streaming_timeout": self.streaming_timeout,
            "conflate_ms": self.conflate_ms,
            "stream_ids": self.stream_ids,
            "max_selection_exposure": self.max_selection_exposure,
            "max_order_exposure": self.max_order_exposure,
            "max_live_trade_count": self.max_live_trade_count,
            "max_trade_count": self.max_trade_count,
            "context": self.context,
            "name_hash": self.name_hash,
        }

    @property
    def name(self) -> str:
        return self._name or self.__class__.__name__

    def __str__(self):
        return "{0}".format(self.name)


class Strategies:
    def __init__(self):
        self._strategies = []

    def __call__(self, strategy: BaseStrategy, clients) -> None:
        if strategy.name in [s.name for s in self]:
            logger.warning("Strategy of same name '{0}' already added".format(strategy))
        strategy.clients = clients
        self._strategies.append(strategy)
        strategy.add()

    def start(self) -> None:
        for s in self:
            s.start()

    def finish(self, flumine) -> None:
        for s in self:
            s.finish(flumine)

    @property
    def hashes(self) -> dict:
        return {strategy.name_hash: strategy for strategy in self}

    def __iter__(self) -> Iterator[BaseStrategy]:
        return iter(self._strategies)

    def __len__(self) -> int:
        return len(self._strategies)
