import time
import queue
import logging
from betdaq import BetdaqError
from tenacity import retry

from .basestream import BaseStream
from ..clients import ExchangeType
from ..events.events import CurrentOrdersEvent
from .. import config

logger = logging.getLogger(__name__)

RETRY_WAIT = BaseStream.RETRY_WAIT
START_DELAY = 2
SNAP_DELTA = 5


class BetdaqOrderPolling(BaseStream):
    @retry(wait=RETRY_WAIT)
    def run(self) -> None:
        logger.info(
            "Starting BetdaqOrderPolling %s",
            self.stream_id,
            extra={
                "stream_id": self.stream_id,
                "client_username": self.client.username,
            },
        )
        sequence_number = 0
        # todo bootstrap call first?
        while True:
            try:
                current_orders = self.betting_client.betting.get_orders_diff(
                    SequenceNumber=sequence_number
                )
            except (BetdaqError, Exception) as e:
                logger.error(
                    "BetdaqOrderPolling %s run error", self.stream_id, exc_info=True
                )
                continue

            if current_orders or self.flumine.markets.live_orders:
                # update SequenceNumber
                for order in current_orders:
                    sequence_number = max(order["sequence_number"], sequence_number)

                self.flumine.handler_queue.put(
                    CurrentOrdersEvent(current_orders, exchange=ExchangeType.BETDAQ)
                )

            time.sleep(2)  # todo update / check for live betdaq orders?

    @property
    def stream_running(self) -> bool:
        return True
