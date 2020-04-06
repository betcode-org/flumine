import threading
import queue
import logging
import betfairlightweight
from betfairlightweight import StreamListener
from betfairlightweight import BetfairError
from tenacity import retry, wait_exponential

from ..event.event import MarketBookEvent

logger = logging.getLogger(__name__)


class BaseStream(threading.Thread):

    LISTENER = StreamListener
    MAX_LATENCY = 0.5

    def __init__(
        self,
        flumine,
        stream_id: int,
        market_filter: dict,
        market_data_filter: dict,
        streaming_timeout: float,  # snaps listener if no update
        conflate_ms: int,
    ):
        threading.Thread.__init__(self, daemon=True, name=self.__class__.__name__)
        self.flumine = flumine
        self.stream_id = stream_id
        self.market_filter = market_filter
        self.market_data_filter = market_data_filter
        self.streaming_timeout = streaming_timeout
        self.conflate_ms = conflate_ms
        self._stream = None
        self._output_queue = queue.Queue()
        self._listener = self.LISTENER(
            output_queue=self._output_queue, max_latency=self.MAX_LATENCY
        )
        self._output_thread = threading.Thread(
            name="{0}_output_thread".format(self._name),
            target=self.handle_output,
            daemon=True,
        )

    def run(self) -> None:
        raise NotImplementedError

    def handle_output(self) -> None:
        raise NotImplementedError

    def stop(self) -> None:
        if self._stream:
            self._stream.stop()

    @property
    def betting_client(self) -> betfairlightweight.APIClient:
        return self.flumine.client.betting_client
