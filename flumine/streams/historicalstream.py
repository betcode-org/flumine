import logging
from betfairlightweight.streaming import HistoricalGeneratorStream

from .basestream import BaseStream
from ..backtest.listener import HistoricListener

logger = logging.getLogger(__name__)


class HistoricalStream(BaseStream):

    MAX_LATENCY = None

    def run(self) -> None:
        pass

    def handle_output(self) -> None:
        pass

    def create_generator(self):
        listener = HistoricListener(
            output_queue=self._output_queue,
            max_latency=self.MAX_LATENCY,
            inplay=True
        )
        listener.register_stream(0, "marketSubscription")
        stream = HistoricalGeneratorStream(
            directory=self.market_filter, listener=listener
        )
        return stream.get_generator()
