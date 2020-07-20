import time
import logging

from .basestream import BaseStream
from ..events.events import CurrentOrdersEvent

logger = logging.getLogger(__name__)


class SimulatedOrderStream(BaseStream):
    def run(self) -> None:
        logger.info("Starting SimulatedOrderStream")

        while self.is_alive():
            if self.flumine.markets.live_orders:
                current_orders = []
                for market in self.flumine.markets:
                    if market.closed is False:
                        for order in market.blotter:
                            if order.simulated:
                                current_orders.append(order.current_order)

                if current_orders:
                    print(current_orders)
                    self.flumine.handler_queue.put(CurrentOrdersEvent(current_orders))

            time.sleep(self.streaming_timeout)

        logger.info("Stopped SimulatedOrderStream {0}".format(self.stream_id))
