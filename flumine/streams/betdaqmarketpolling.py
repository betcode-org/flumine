import time
import logging
from betdaq import BetdaqError
from tenacity import retry

from .basestream import BaseStream
from ..clients import VenueType
from ..events.events import MarketBookEvent

logger = logging.getLogger(__name__)

RETRY_WAIT = BaseStream.RETRY_WAIT
START_DELAY = 2
SNAP_DELTA = 2


class BetdaqMarketPolling(BaseStream):
    @retry(wait=RETRY_WAIT)
    def run(self) -> None:
        logger.info(
            f"Starting BetdaqMarketPolling '{self.stream_id}'",
            extra={
                "stream_id": self.stream_id,
                "client_username": self.client.username,
            },
        )

        while self.is_alive():
            try:
                # todo chunk
                prices = self.betting_client.marketdata.get_prices(**self.market_filter)
            except (BetdaqError, Exception):
                logger.error(
                    "BetdaqMarketPolling %s run error", self.stream_id, exc_info=True
                )
                time.sleep(SNAP_DELTA)
                continue

            # todo add streaming_unique_id
            self.flumine.handler_queue.put(
                MarketBookEvent(prices, venue=VenueType.BETDAQ)
            )
            time.sleep(self.streaming_timeout)

        logger.info(
            f"Stopped BetdaqMarketPolling '{self.stream_id}'",
            extra={
                "stream_id": self.stream_id,
                "client_username": self.client.username,
            },
        )

    @property
    def stream_running(self) -> bool:
        return True
