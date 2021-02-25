import logging
from tenacity import retry
from betfairlightweight import StreamListener
from betfairlightweight import BetfairError
from betfairlightweight.streaming.stream import BaseStream as BFBaseStream

from .basestream import BaseStream
from ..events.events import RawDataEvent
from ..exceptions import ListenerError

logger = logging.getLogger(__name__)

RETRY_WAIT = BaseStream.RETRY_WAIT


"""
Custom listener that doesn't do any processing,
helps reduce CPU.
"""


class FlumineListener(StreamListener):
    def _add_stream(self, unique_id: int, operation: str) -> BFBaseStream:
        if operation == "marketSubscription":
            return FlumineMarketStream(self, unique_id)
        elif operation == "orderSubscription":
            raise ListenerError("Unable to process order stream")
        elif operation == "raceSubscription":
            return FlumineRaceStream(self, unique_id)


class FlumineStream(BFBaseStream):
    def on_process(self, caches: list) -> None:
        output = RawDataEvent(caches)
        self.output_queue.put(output)

    def __str__(self):
        return "FlumineStream"

    def __repr__(self):
        return "<FlumineStream [%s]>" % len(self._caches)


class FlumineMarketStream(FlumineStream):

    _lookup = "mc"

    def _process(self, data: list, publish_time: int) -> bool:
        for market_book in data:
            market_id = market_book.get("id")
            if (
                "marketDefinition" in market_book
                and market_book["marketDefinition"]["status"] == "CLOSED"
            ):
                if market_id in self._caches:
                    # removes closed market from cache
                    del self._caches[market_id]
                    logger.info(
                        "[MarketStream: %s] %s removed, %s markets in cache"
                        % (self.unique_id, market_id, len(self._caches))
                    )
            elif self._caches.get(market_id) is None:
                # adds empty object to cache to track live market count
                self._caches[market_id] = object()
                logger.info(
                    "[MarketStream: %s] %s added, %s markets in cache"
                    % (self.unique_id, market_id, len(self._caches))
                )
            self._updates_processed += 1

        self.on_process([self.unique_id, publish_time, data])
        return False


class FlumineRaceStream(FlumineStream):

    _lookup = "rc"

    def _process(self, data: list, publish_time: int) -> bool:
        for update in data:
            market_id = update["mid"]
            if self._caches.get(market_id) is None:
                # adds empty object to cache to track live market count
                self._caches[market_id] = object()
                logger.info(
                    "[RaceStream: %s] %s added, %s markets in cache"
                    % (self.unique_id, market_id, len(self._caches))
                )
            self._updates_processed += 1

        self.on_process([self.unique_id, publish_time, data])
        return False


class DataStream(BaseStream):

    LISTENER = FlumineListener

    def __init__(self, *args, **kwargs):
        BaseStream.__init__(self, *args, **kwargs)
        self._listener = self.LISTENER(output_queue=self.flumine.handler_queue)

    @retry(wait=RETRY_WAIT)
    def run(self) -> None:
        logger.info(
            "Starting DataStream {0}".format(self.stream_id),
            extra={
                "stream_id": self.stream_id,
                "market_filter": self.market_filter,
                "market_data_filter": self.market_data_filter,
                "conflate_ms": self.conflate_ms,
            },
        )

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
                "DataStream {0} run error".format(self.stream_id), exc_info=True
            )
            raise
        except Exception:
            logger.critical(
                "DataStream {0} run error".format(self.stream_id), exc_info=True
            )
            raise
        logger.info("Stopped DataStream {0}".format(self.stream_id))
