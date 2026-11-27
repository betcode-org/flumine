import time
import logging
from tenacity import retry

from .basestream import BaseStream
from ..clients import VenueType
from ..events.events import CurrentOrdersEvent

logger = logging.getLogger(__name__)

RETRY_WAIT = BaseStream.RETRY_WAIT
START_DELAY = 2
SNAP_DELTA = 2


class MatchbookOrderPolling(BaseStream):
    VENUE = VenueType.MATCHBOOK

    @retry(wait=RETRY_WAIT)
    def run(self) -> None:
        logger.info(
            f"Starting MatchbookOrderPolling '{self.stream_id}'",
            extra={
                "stream_id": self.stream_id,
                "client_username": self.client.username,
            },
        )
        time.sleep(5)  # wait for markets

        while self.is_alive():
            try:
                current_orders = self.betting_client.get_offers(per_page=1024)
            except Exception:
                logger.error(
                    "MatchbookOrderPolling %s run error", self.stream_id, exc_info=True
                )
                time.sleep(SNAP_DELTA)
                continue

            self._process_current_orders(current_orders.offers)

            if self.flumine.markets.live_orders:
                time.sleep(self.streaming_timeout)
            else:
                # immediately exits sleep if an order is placed
                self.flumine.markets.live_orders_event.wait(timeout=SNAP_DELTA)

        logger.info(
            f"Stopped MatchbookOrderPolling '{self.stream_id}'",
            extra={
                "stream_id": self.stream_id,
                "client_username": self.client.username,
            },
        )

    def _process_current_orders(self, current_orders: list):
        if current_orders or self.flumine.markets.live_orders:
            self.flumine.handler_queue.put(
                CurrentOrdersEvent(current_orders, venue=self.VENUE)
            )

    @property
    def stream_running(self) -> bool:
        return True
