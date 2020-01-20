from ..strategy.strategy import BaseStrategy


class Streams:
    def __init__(self):
        self._streams = []
        self._stream_id = 0

    def __call__(self, strategy: BaseStrategy):
        pass

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
