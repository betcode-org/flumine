import logging
from typing import Union, Iterator

from ..strategy.strategy import BaseStrategy
from .marketstream import MarketStream
from .datastream import DataStream
from .historicalstream import HistoricalStream
from .orderstream import OrderStream
from .simulatedorderstream import SimulatedOrderStream
from ..clients import ExchangeType, BaseClient

logger = logging.getLogger(__name__)


class Streams:
    def __init__(self, flumine):
        self.flumine = flumine
        self._streams = []
        self._stream_id = 0

    def __call__(self, strategy: BaseStrategy) -> None:
        if self.flumine.BACKTEST:
            markets = strategy.market_filter.get("markets")
            listener_kwargs = strategy.market_filter.get("listener_kwargs", {})
            if markets is None:
                logging.warning("No markets found for strategy {0}".format(strategy))
            else:
                for market in markets:
                    stream = self.add_historical_stream(
                        strategy, market, **listener_kwargs
                    )
                    strategy.streams.append(stream)
        else:
            stream = self.add_stream(strategy)
            strategy.streams.append(stream)

    def add_client(self, client: BaseClient) -> None:
        if client.order_stream:
            if client.paper_trade:
                self.add_simulated_order_stream(client)
            elif client.EXCHANGE == ExchangeType.BETFAIR:
                self.add_order_stream(client)

    """ market data """

    def add_stream(self, strategy: BaseStrategy) -> Union[MarketStream, DataStream]:
        for stream in self:  # check if market stream already exists
            if (
                isinstance(stream, strategy.stream_class)
                and stream.market_filter == strategy.market_filter
                and stream.market_data_filter == strategy.market_data_filter
                and stream.streaming_timeout == strategy.streaming_timeout
                and stream.conflate_ms == strategy.conflate_ms
            ):
                logger.info(
                    "Using {0} ({1}) for strategy {2}".format(
                        strategy.stream_class, stream.stream_id, strategy
                    )
                )
                return stream
        else:  # nope? lets create a new one
            stream_id = self._increment_stream_id()
            logger.info(
                "Creating new {0} ({1}) for strategy {2}".format(
                    strategy.stream_class, stream_id, strategy
                )
            )
            stream = strategy.stream_class(
                flumine=self.flumine,
                stream_id=stream_id,
                market_filter=strategy.market_filter,
                market_data_filter=strategy.market_data_filter,
                streaming_timeout=strategy.streaming_timeout,
                conflate_ms=strategy.conflate_ms,
            )
            self._streams.append(stream)
            return stream

    def add_historical_stream(
        self, strategy: BaseStrategy, market, **listener_kwargs
    ) -> HistoricalStream:
        for stream in self:
            if stream.market_filter == market:
                return stream
        else:
            stream_id = self._increment_stream_id()
            logger.info(
                "Creating new {0} ({1}) for strategy {2}".format(
                    HistoricalStream, stream_id, strategy
                )
            )
            stream = HistoricalStream(
                flumine=self.flumine,
                stream_id=stream_id,
                market_filter=market,
                market_data_filter=strategy.market_data_filter,
                streaming_timeout=strategy.streaming_timeout,
                conflate_ms=strategy.conflate_ms,
                output_queue=False,
                **listener_kwargs,
            )
            self._streams.append(stream)
            return stream

    """ order data """

    def add_order_stream(
        self,
        client: BaseClient,
        conflate_ms: int = None,
        streaming_timeout: float = 0.25,
    ) -> OrderStream:
        stream_id = self._increment_stream_id()
        stream = OrderStream(
            flumine=self.flumine,
            stream_id=stream_id,
            conflate_ms=conflate_ms,
            streaming_timeout=streaming_timeout,
            client=client,
        )
        self._streams.append(stream)
        return stream

    def add_simulated_order_stream(
        self,
        client: BaseClient,
        conflate_ms: int = None,
        streaming_timeout: float = 0.25,
    ) -> SimulatedOrderStream:
        logger.warning(
            "Client {0} now paper trading".format(client.betting_client.username)
        )
        stream_id = self._increment_stream_id()
        stream = SimulatedOrderStream(
            flumine=self.flumine,
            stream_id=stream_id,
            conflate_ms=conflate_ms,
            streaming_timeout=streaming_timeout,
            client=client,
        )
        self._streams.append(stream)
        return stream

    def start(self) -> None:
        if not self.flumine.BACKTEST:
            logger.info("Starting streams..")
            for stream in self:
                stream.start()

    def stop(self) -> None:
        for stream in self:
            stream.stop()

    def _increment_stream_id(self) -> int:
        self._stream_id += int(1e3)
        return self._stream_id

    def __iter__(self) -> Iterator[Union[MarketStream, DataStream, HistoricalStream]]:
        return iter(self._streams)

    def __len__(self) -> int:
        return len(self._streams)
