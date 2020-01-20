import threading
import queue
import logging
import betfairlightweight
from betfairlightweight import StreamListener
from betfairlightweight import BetfairError
from tenacity import retry, wait_exponential

from ..event.event import MarketBookEvent

logger = logging.getLogger(__name__)


class MarketStream(threading.Thread):
    def __init__(
        self,
        flumine,
        stream_id: int,
        market_filter: dict,
        market_data_filter: dict,
        streaming_timeout: float,
    ):
        threading.Thread.__init__(self, daemon=True, name=self.__class__.__name__)
        self.flumine = flumine
        self.stream_id = stream_id
        self.market_filter = market_filter
        self.market_data_filter = market_data_filter
        self.streaming_timeout = streaming_timeout
        self._stream = None
        self._output_queue = queue.Queue()
        self._listener = StreamListener(output_queue=self._output_queue)

        self._output_thread = threading.Thread(
            name="{0}_output_thread".format(self._name),
            target=self.handle_output,
            daemon=True,
        )

    @retry(wait=wait_exponential(multiplier=1, min=2, max=20))
    def run(self) -> None:
        logger.info("Starting MarketStreaming")

        if not self._output_thread.is_alive():
            logger.info("Starting output_thread {0}".format(self._output_thread))
            self._output_thread.start()

        self.stream = self.trading.streaming.create_stream(
            unique_id=self.stream_id, listener=self._listener
        )
        try:
            self.streaming_unique_id = self.stream.subscribe_to_markets(
                market_filter=self.market_filter,
                market_data_filter=self.market_data_filter,
                # conflate_ms=self.conflate_ms,
                initial_clk=self._listener.initial_clk,  # supplying these two values allows a reconnect
                clk=self._listener.clk,
            )
            self.stream.start()
        except BetfairError:
            logger.error("MarketStreaming run error", exc_info=True)
            raise
        except Exception:
            logger.critical("MarketStreaming run error", exc_info=True)
            raise
        logger.info("Stopped MarketStreaming {0}".format(self.stream_id))

    def handle_output(self):
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
            "Stopped output_thread (MarketStreaming {0})".format(self.stream_id)
        )

    def stop(self) -> None:
        if self._stream:
            self._stream.stop()

    @property
    def trading(self) -> betfairlightweight.APIClient:
        return self.flumine.trading
