import logging

from .baseflumine import BaseFlumine
from .events.events import EventType
from . import worker

logger = logging.getLogger(__name__)


class Flumine(BaseFlumine):
    def run(self) -> None:
        """
        Main run thread
        """
        with self:
            while True:
                event = self.handler_queue.get()
                if event.EVENT_TYPE == EventType.TERMINATOR:
                    self._process_end_flumine()
                    break

                elif event.EVENT_TYPE == EventType.MARKET_CATALOGUE:
                    self._process_market_catalogues(event)

                elif event.EVENT_TYPE == EventType.MARKET_BOOK:
                    self._process_market_books(event)

                elif event.EVENT_TYPE == EventType.RAW_DATA:
                    self._process_raw_data(event)

                elif event.EVENT_TYPE == EventType.CURRENT_ORDERS:
                    self._process_current_orders(event)

                elif event.EVENT_TYPE == EventType.ORDER_PACKAGE:
                    self._process_order_package(event)

                elif event.EVENT_TYPE == EventType.CLEARED_MARKETS:
                    self._process_cleared_markets(event)

                elif event.EVENT_TYPE == EventType.CLEARED_ORDERS:
                    self._process_cleared_orders(event)

                elif event.EVENT_TYPE == EventType.CLOSE_MARKET:
                    self._process_close_market(event)

                elif event.EVENT_TYPE == EventType.CUSTOM_EVENT:
                    self._process_custom_event(event)

                elif event.EVENT_TYPE == EventType.NEW_DAY:
                    logger.info(event)

                else:
                    logger.error("Unknown item in handler_queue: %s" % str(event))

    def _add_default_workers(self):
        self.add_worker(
            worker.BackgroundWorker(self, function=worker.keep_alive, interval=1200)
        )
        self.add_worker(
            worker.BackgroundWorker(
                self,
                function=worker.poll_account_balance,
                interval=120,
                start_delay=10,  # wait for login
            )
        )
        self.add_worker(
            worker.BackgroundWorker(
                self,
                function=worker.poll_market_catalogue,
                interval=60,
                start_delay=10,  # wait for streams to populate
            )
        )
        self.add_worker(
            worker.BackgroundWorker(
                self,
                function=worker.poll_cleared_orders,
                interval=10,  # restart
                start_delay=10,  # wait for login
            )
        )

    def __repr__(self) -> str:
        return "<Flumine>"

    def __str__(self) -> str:
        return "<Flumine>"
