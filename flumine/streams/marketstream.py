import queue
import logging
from betfairlightweight import BetfairError
from tenacity import retry, wait_exponential

from .basestream import BaseStream
from ..events.events import MarketBookEvent

logger = logging.getLogger(__name__)


class MarketStream(BaseStream):
    @retry(wait=wait_exponential(multiplier=1, min=2, max=20))
    def run(self) -> None:
        logger.info(
            "Starting MarketStream {0}".format(self.stream_id),
            extra={
                "stream_id": self.stream_id,
                "market_filter": self.market_filter,
                "market_data_filter": self.market_data_filter,
                "conflate_ms": self.conflate_ms,
                "streaming_timeout": self.streaming_timeout,
            },
        )
        if not self._output_thread.is_alive():
            logger.info(
                "Starting output_thread (MarketStream {0})".format(self.stream_id)
            )
            self._output_thread.start()

        self._stream = self.betting_client.streaming.create_stream(
            unique_id=self.stream_id, listener=self._listener
        )
        try:
            self.stream_id = self._stream.subscribe_to_markets(
                market_filter=self.market_filter,
                market_data_filter=self.market_data_filter,
                conflate_ms=self.conflate_ms,
                initial_clk=self._listener.initial_clk,  # supplying these two values allows a reconnect
                clk=self._listener.clk,
            )
            self._stream.start()
        except BetfairError:
            logger.error(
                "MarketStream {0} run error".format(self.stream_id), exc_info=True
            )
            raise
        except Exception:
            logger.critical(
                "MarketStream {0} run error".format(self.stream_id), exc_info=True
            )
            raise
        logger.info("Stopped MarketStream {0}".format(self.stream_id))

    def handle_output(self) -> None:
        """Handles output from stream."""
        while self.is_alive():
            try:
                market_books = self._output_queue.get(
                    block=True, timeout=self.streaming_timeout
                )
            except queue.Empty:
                market_books = self._listener.snap(
                    market_ids=self.flumine.markets.open_market_ids
                )
            if market_books:
                self.flumine.handler_queue.put(MarketBookEvent(market_books))

        logger.info("Stopped output_thread (MarketStream {0})".format(self.stream_id))
