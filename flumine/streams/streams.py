import time
import logging
from typing import Union, Iterator

from .betfairmarketstream import BetfairMarketStream
from .betfairdatastream import BetfairDataStream
from .betfairhistoricalstream import BetfairHistoricalStream
from .betfairorderstream import BetfairOrderStream
from .simulatedorderstream import SimulatedOrderStream
from .betdaqorderpolling import BetdaqOrderPolling
from ..clients import VenueType, BaseClient
from ..exceptions import StreamError

logger = logging.getLogger(__name__)


class Streams:
    def __init__(self, flumine):
        self.flumine = flumine
        self._streams = []
        self._stream_id = 0

    def add_client(self, client: BaseClient) -> None:
        if client.order_stream:
            if client.order_stream_cls:
                order_stream = client.order_stream_cls(
                    flumine=self.flumine,
                    client=client,
                    custom=True,
                )
                self.add_stream(order_stream)
            else:
                if client.paper_trade:
                    self.add_simulated_order_stream(
                        client, streaming_timeout=client.order_streaming_timeout
                    )
                elif client.VENUE == VenueType.BETFAIR:
                    self.add_betfair_order_stream(
                        client,
                        conflate_ms=client.order_stream_conflate_ms,
                        streaming_timeout=client.order_streaming_timeout,
                    )
                elif client.VENUE == VenueType.BETDAQ:
                    self.add_betdaq_order_polling(
                        client, streaming_timeout=client.order_streaming_timeout
                    )

    """ market data """

    def add_stream(self, stream):
        if stream in self._streams:
            logger.info(f"Stream {stream} already added, reusing")
            return stream
        stream.stream_id = self._increment_stream_id()
        self._streams.append(stream)
        return stream

    """ order data """

    def add_betfair_order_stream(
        self,
        client: BaseClient,
        conflate_ms: int = None,
        streaming_timeout: float = 0.25,
    ) -> BetfairOrderStream:
        stream = BetfairOrderStream(
            flumine=self.flumine,
            conflate_ms=conflate_ms,
            streaming_timeout=streaming_timeout,
            client=client,
        )
        return self.add_stream(stream)

    def add_simulated_order_stream(
        self,
        client: BaseClient,
        conflate_ms: int = None,
        streaming_timeout: float = 0.25,
    ) -> SimulatedOrderStream:
        logger.warning("Client %s now paper trading", client.betting_client.username)
        stream = SimulatedOrderStream(
            flumine=self.flumine,
            conflate_ms=conflate_ms,
            streaming_timeout=streaming_timeout,
            client=client,
            custom=True,
        )
        return self.add_stream(stream)

    def add_betdaq_order_polling(
        self,
        client: BaseClient,
        streaming_timeout: float = 0.25,
    ) -> BetdaqOrderPolling:
        stream = BetdaqOrderPolling(
            flumine=self.flumine,
            client=client,
            streaming_timeout=streaming_timeout,
        )
        return self.add_stream(stream)

    def start(self) -> None:
        if not self.flumine.SIMULATED:
            logger.info("Starting streams..")
            for stream in self:
                stream.start()
                # wait for successful start
                while not stream.custom and not stream.stream_running:
                    time.sleep(0.25)
                time.sleep(0.5)  # prevent an SSL lock

    def stop(self) -> None:
        for stream in self:
            stream.stop()

    def _increment_stream_id(self) -> int:
        self._stream_id += int(1e4)
        return self._stream_id

    def __iter__(
        self,
    ) -> Iterator[
        Union[BetfairMarketStream, BetfairDataStream, BetfairHistoricalStream]
    ]:
        return iter(self._streams)

    def __len__(self) -> int:
        return len(self._streams)
