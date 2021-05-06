import threading
import queue
import logging
import betfairlightweight
from betfairlightweight import StreamListener
from tenacity import wait_exponential

logger = logging.getLogger(__name__)


class BaseStream(threading.Thread):

    LISTENER = StreamListener
    MAX_LATENCY = 0.5
    RETRY_WAIT = wait_exponential(multiplier=1, min=2, max=60)

    def __init__(
        self,
        flumine,
        stream_id: int,
        streaming_timeout: float,  # snaps listener if no update
        conflate_ms: int,
        market_filter: dict = None,
        market_data_filter: dict = None,
        client=None,
        output_queue: bool = True,
        event_processing: bool = False,
        event_id: str = None,
        operation: str = "marketSubscription",
        **listener_kwargs,
    ):
        threading.Thread.__init__(self, daemon=True, name=self.__class__.__name__)
        self.flumine = flumine
        self.stream_id = stream_id
        self.market_filter = market_filter
        self.market_data_filter = market_data_filter
        self.streaming_timeout = streaming_timeout
        self.conflate_ms = conflate_ms
        self._client = client
        self._stream = None
        self._output_queue = queue.Queue() if output_queue else None
        self.event_processing = event_processing
        self.event_id = event_id
        self.operation = operation
        self._listener = self.LISTENER(
            output_queue=self._output_queue,
            max_latency=self.MAX_LATENCY,
            **listener_kwargs,
        )
        self._output_thread = threading.Thread(
            name="{0}_output_thread".format(self.name),
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
        return self.client.betting_client

    @property
    def client(self):
        if self._client:
            return self._client
        else:
            return self.flumine.client
