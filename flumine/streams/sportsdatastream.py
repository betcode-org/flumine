import time
import queue
import logging
from betfairlightweight import BetfairError
from tenacity import retry

from .basestream import BaseStream
from ..events.events import SportsDataEvent

logger = logging.getLogger(__name__)

RETRY_WAIT = BaseStream.RETRY_WAIT


class SportsDataStream(BaseStream):
    @retry(wait=RETRY_WAIT)
    def run(self) -> None:
        time.sleep(2)  # 2s delay to wait for market streams to start
        logger.info(
            "Starting SportsDataStream {0}".format(self.stream_id),
            extra={
                "stream_id": self.stream_id,
                "sports_data_filter": self.sports_data_filter,
                "streaming_timeout": self.streaming_timeout,
            },
        )
        if not self._output_thread.is_alive():
            logger.info(
                "Starting output_thread (SportsDataStream {0})".format(self.stream_id)
            )
            self._output_thread.start()

        self._stream = self.betting_client.streaming.create_stream(
            unique_id=self.stream_id, host="sports_data", listener=self._listener
        )
        try:
            if self.sports_data_filter == "raceSubscription":
                self.stream_id = self._stream.subscribe_to_races()
            elif self.sports_data_filter == "cricketSubscription":
                self.stream_id = self._stream.subscribe_to_cricket_matches()
            else:
                raise ValueError("Unknown sports data filter")
            self._stream.start()
        except BetfairError:
            logger.error(
                "SportsDataStream {0} run error".format(self.stream_id), exc_info=True
            )
            raise
        except Exception:
            logger.critical(
                "SportsDataStream {0} run error".format(self.stream_id), exc_info=True
            )
            raise
        logger.info("Stopped SportsDataStream {0}".format(self.stream_id))

    def handle_output(self) -> None:
        """Handles output from stream."""
        while self.is_alive():
            try:
                sports_data = self._output_queue.get(
                    block=True, timeout=self.streaming_timeout
                )
            except queue.Empty:
                sports_data = self._listener.snap(
                    market_ids=self.flumine.markets.open_market_ids
                )
            if sports_data:
                self.flumine.handler_queue.put(SportsDataEvent(sports_data))

        logger.info(
            "Stopped output_thread (SportsDataStream {0})".format(self.stream_id)
        )
