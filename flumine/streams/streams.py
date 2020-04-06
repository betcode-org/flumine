import logging
from typing import Union, Iterator

from ..strategy.strategy import BaseStrategy
from .marketstream import MarketStream
from .datastream import DataStream
from .historicalstream import HistoricalStream

logger = logging.getLogger(__name__)


class Streams:
    def __init__(self, flumine):
        self.flumine = flumine
        self._streams = []
        self._stream_id = 0

    def __call__(self, strategy: BaseStrategy) -> None:
        if self.flumine.BACKTEST:
            markets = strategy.market_filter.get("markets")
            if markets is None:
                logging.warning("No markets found for strategy {0}".format(strategy))
            else:
                for market in markets:
                    stream = self.add_historical_stream(strategy, market)
                    strategy.streams.append(stream)
        else:
            stream = self.add_stream(strategy)
            strategy.streams.append(stream)

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

    def add_historical_stream(self, strategy, market):
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
