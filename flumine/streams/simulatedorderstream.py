import time
import logging

from .basestream import BaseStream
from ..events.events import CurrentOrdersEvent

logger = logging.getLogger(__name__)


class CurrentOrders:
    def __init__(self, orders, client):
        self.orders = orders
        self.more_available = False
        self.client = client


class SimulatedOrderStream(BaseStream):
    def run(self) -> None:
        logger.info(
            "Starting SimulatedOrderStream %s",
            self.stream_id,
            extra={
                "stream_id": self.stream_id,
                "streaming_timeout": self.streaming_timeout,
            },
        )

        while self.is_alive():
            if self.flumine.markets.live_orders:
                current_orders = self._get_current_orders()
                if current_orders:
                    self.flumine.handler_queue.put(
                        CurrentOrdersEvent([CurrentOrders(current_orders, self.client)])
                    )
            time.sleep(self.streaming_timeout)
        logger.info("Stopped SimulatedOrderStream %s", self.stream_id)

    def _get_current_orders(self) -> list:
        current_orders = []
        for market in self.flumine.markets:
            if market.closed is False:
                current_orders += market.blotter.client_orders(self.client)
        return current_orders
