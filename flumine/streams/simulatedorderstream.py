import time
import logging

from .basestream import BaseStream
from ..events.events import CurrentOrdersEvent

logger = logging.getLogger(__name__)


class CurrentOrders:
    def __init__(self, orders):
        self.orders = orders
        self.more_available = False


class SimulatedOrderStream(BaseStream):
    def run(self) -> None:
        logger.info("Starting SimulatedOrderStream")

        while self.is_alive():
            if self.flumine.markets.live_orders:
                current_orders = self._get_current_orders()
                if current_orders:
                    self.flumine.handler_queue.put(
                        CurrentOrdersEvent([CurrentOrders(current_orders)])
                    )
            time.sleep(self.streaming_timeout)
        logger.info("Stopped SimulatedOrderStream {0}".format(self.stream_id))

    def _get_current_orders(self) -> list:
        current_orders = []
        for market in self.flumine.markets:
            if market.closed is False:
                for order in market.blotter:
                    if order.simulated and order.trade.client == self.client:
                        current_orders.append(order)
        return current_orders
