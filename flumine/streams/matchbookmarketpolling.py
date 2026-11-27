import datetime
import time
import logging

from tenacity import retry

from .basestream import BaseStream
from ..clients import VenueType
from ..events.events import MarketBookEvent

logger = logging.getLogger(__name__)

RETRY_WAIT = BaseStream.RETRY_WAIT
START_DELAY = 2
SNAP_DELTA = 2


class MatchbookMarketPolling(BaseStream):
    VENUE = VenueType.MATCHBOOK

    @retry(wait=RETRY_WAIT)
    def run(self) -> None:
        logger.info(
            f"Starting MatchbookMarketPolling '{self.stream_id}'",
            extra={
                "stream_id": self.stream_id,
                "client_username": self.client.username,
            },
        )

        while self.is_alive():
            try:
                events = self.betting_client.get_events(**self.market_filter)
            except Exception:
                logger.error(
                    "MatchbookMarketPolling %s run error", self.stream_id, exc_info=True
                )
                time.sleep(SNAP_DELTA)
                continue

            markets = [m for event in events.events for m in event.markets if m]

            # for market in markets:
            #     market.publish_time = datetime.datetime.now(tz=datetime.timezone.utc)
            #     market.streaming_unique_id = self.stream_id

            self.flumine.handler_queue.put(
                MarketBookEvent(
                    markets, venue=self.VENUE, streaming_unique_id=self.stream_id
                )
            )
            time.sleep(self.streaming_timeout or 1)

        logger.info(
            f"Stopped MatchbookMarketPolling '{self.stream_id}'",
            extra={
                "stream_id": self.stream_id,
                "client_username": self.client.username,
            },
        )

    @property
    def stream_running(self) -> bool:
        return True
