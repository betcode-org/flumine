from ..strategy.strategy import BaseStrategy
from .marketstream import MarketStream


class Streams:
    def __init__(self, flumine):
        self.flumine = flumine
        self._streams = []
        self._stream_id = 0

    def __call__(self, strategy: BaseStrategy):
        stream = self._add_market_stream(strategy)
        strategy.streams.append(stream)

    def _add_market_stream(self, strategy: BaseStrategy) -> MarketStream:
        # check if market stream already exists
        for stream in self:
            if (
                isinstance(stream, MarketStream)
                and stream.market_filter == strategy.market_filter
                and stream.market_data_filter == strategy.market_data_filter
            ):
                return stream
        else:  # nope? lets create a new one
            stream_id = self._increment_stream_id()
            stream = MarketStream(
                self.flumine,
                stream_id,
                strategy.market_filter,
                strategy.market_data_filter,
                strategy.streaming_timeout,
            )
            self._streams.append(stream)
            return stream

    def start(self) -> None:
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
