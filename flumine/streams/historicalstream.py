import logging
from betfairlightweight.streaming import HistoricalGeneratorStream

from .basestream import BaseStream

logger = logging.getLogger(__name__)


class HistoricalStream(BaseStream):

    MAX_LATENCY = None

    def run(self) -> None:
        pass

    def handle_output(self) -> None:
        pass

    def create_generator(self):
        self._listener.output_queue = None
        self._listener.register_stream(0, "marketSubscription")
        stream = HistoricalGeneratorStream(
            directory=self.market_filter, listener=self._listener
        )
        return stream.get_generator()
