import time
import logging
from betdaq import BetdaqError
from tenacity import retry

from .basestream import BaseStream
from ..clients import ExchangeType
from ..events.events import CurrentOrdersEvent

logger = logging.getLogger(__name__)

RETRY_WAIT = BaseStream.RETRY_WAIT
START_DELAY = 2
SNAP_DELTA = 2


class BetdaqOrderPolling(BaseStream):
    @retry(wait=RETRY_WAIT)
    def run(self) -> None:
        logger.info(
            f"Starting BetdaqOrderPolling '{self.stream_id}'",
            extra={
                "stream_id": self.stream_id,
                "client_username": self.client.username,
            },
        )
        # bootstrap call first to get most recent sequence number and all current orders
        order_count, sequence_number = 251, 0
        while order_count > 250:  # continue to call until less than 250 orders returned
            bootstrap = self.betting_client.betting.get_orders()
            current_orders = bootstrap["orders"]
            sequence_number = bootstrap["maximum_sequence_number"]
            self._process_current_orders(current_orders, sequence_number)
            order_count = len(current_orders)

        while self.is_alive():
            try:
                current_orders = self.betting_client.betting.get_orders_diff(
                    SequenceNumber=sequence_number
                )
            except (BetdaqError, Exception):
                logger.error(
                    "BetdaqOrderPolling %s run error", self.stream_id, exc_info=True
                )
                time.sleep(SNAP_DELTA)
                continue
            sequence_number = self._process_current_orders(
                current_orders, sequence_number
            )
            if self.flumine.markets.live_orders:
                time.sleep(self.streaming_timeout)
            else:
                time.sleep(SNAP_DELTA)

        logger.info(
            f"Stopped BetdaqOrderPolling '{self.stream_id}'",
            extra={
                "stream_id": self.stream_id,
                "client_username": self.client.username,
            },
        )

    def _process_current_orders(
        self, current_orders: list, sequence_number: int
    ) -> int:
        if current_orders or self.flumine.markets.live_orders:
            self.flumine.handler_queue.put(
                CurrentOrdersEvent(current_orders, exchange=ExchangeType.BETDAQ)
            )
            # update SequenceNumber
            for order in current_orders:
                sequence_number = max(order["sequence_number"], sequence_number)
        return sequence_number

    @property
    def stream_running(self) -> bool:
        return True
