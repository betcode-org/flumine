import logging
from typing import Union

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
        stream = self.add_stream(strategy)
        strategy.streams.append(stream)

    def add_stream(
        self, strategy: BaseStrategy
    ) -> Union[MarketStream, DataStream, HistoricalStream]:
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

    def start(self) -> None:
        logger.info("Starting streams..")
        for stream in self:
            stream.start()

    def stop(self) -> None:
        for stream in self:
            stream.stop()

    def _increment_stream_id(self) -> int:
        self._stream_id += int(1e3)
        return self._stream_id

    def __iter__(self):
        return iter(self._streams)

    def __len__(self):
        return len(self._streams)
