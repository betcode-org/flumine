import logging
from typing import Union, Type

from ..strategy.strategy import BaseStrategy
from .marketstream import MarketStream
from .datastream import DataStream

logger = logging.getLogger(__name__)


class Streams:
    def __init__(self, flumine):
        self.flumine = flumine
        self._streams = []
        self._stream_id = 0

    def __call__(self, strategy: BaseStrategy) -> None:
        if strategy.raw_data:
            stream = self.add_market_stream(strategy, DataStream)
        else:
            stream = self.add_market_stream(strategy, MarketStream)
        strategy.streams.append(stream)

    def add_market_stream(
        self,
        strategy: BaseStrategy,
        stream_class: Union[Type[MarketStream], Type[DataStream]],
    ) -> Union[MarketStream, DataStream]:
        for stream in self:  # check if market stream already exists
            if (
                isinstance(stream, stream_class)
                and stream.market_filter == strategy.market_filter
                and stream.market_data_filter == strategy.market_data_filter
                and stream.streaming_timeout == strategy.streaming_timeout
                and stream.conflate_ms == strategy.conflate_ms
            ):
                logger.info("Using stream ({0}) for strategy {1}".format(stream.stream_id, strategy))
                return stream
        else:  # nope? lets create a new one
            stream_id = self._increment_stream_id()
            logger.info("Creating new stream ({0}) for strategy {1}".format(stream_id, strategy))
            stream = stream_class(
                self.flumine,
                stream_id,
                strategy.market_filter,
                strategy.market_data_filter,
                strategy.streaming_timeout,
                strategy.conflate_ms,
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
