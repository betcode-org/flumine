import queue
import logging
from betfairlightweight import StreamListener
from betfairlightweight import BetfairError
from tenacity import retry, wait_exponential

from .basestream import BaseStream
from ..event.event import MarketBookEvent

logger = logging.getLogger(__name__)


class HistoricalStream(BaseStream):

    MAX_LATENCY = 1e100

    @retry(wait=wait_exponential(multiplier=1, min=2, max=20))
    def run(self) -> None:
        logger.info("Starting HistoricalStream")
        self.stream_id = 0  # default for historical data

        if not self._output_thread.is_alive():
            logger.info("Starting output_thread {0}".format(self._output_thread))
            self._output_thread.start()

        for market in self.market_filter["markets"]:
            self._stream = self.trading.streaming.create_historical_stream(
                directory=market, listener=self._listener
            )
            try:
                self._stream.start()
            except BetfairError:
                logger.error("HistoricalStream run error", exc_info=True)
                raise
            except Exception:
                logger.critical("HistoricalStream run error", exc_info=True)
                raise
        logger.info("Stopped HistoricalStream {0}".format(self.stream_id))

    def handle_output(self) -> None:
        """Handles output from stream.
        """
        while self.is_alive():
            try:
                market_books = self._output_queue.get(
                    block=True, timeout=self.streaming_timeout
                )
            except queue.Empty:
                market_books = self._listener.snap(
                    market_ids=self.flumine.live_markets.open_markets()
                )
            self.flumine.handler_queue.put(MarketBookEvent(market_books))

        logger.info(
            "Stopped output_thread (HistoricalStream {0})".format(self.stream_id)
        )
