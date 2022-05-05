import logging

from .baseflumine import BaseFlumine
from .events.events import EventType
from . import worker

logger = logging.getLogger(__name__)

MARKET_BOOK_EVENT = EventType.MARKET_BOOK
CURRENT_ORDERS_EVENT = EventType.CURRENT_ORDERS
SPORTS_DATA_EVENT = EventType.SPORTS_DATA
CUSTOM_EVENT_EVENT = EventType.CUSTOM_EVENT
RAW_DATA_EVENT = EventType.RAW_DATA
MARKET_CATALOGUE_EVENT = EventType.MARKET_CATALOGUE
CLEARED_MARKETS_EVENT = EventType.CLEARED_MARKETS
CLEARED_ORDERS_EVENT = EventType.CLEARED_ORDERS
CLOSE_MARKET_EVENT = EventType.CLOSE_MARKET
TERMINATOR_EVENT = EventType.TERMINATOR


class Flumine(BaseFlumine):
    def run(self) -> None:
        """
        Main run thread
        """
        handler_queue_get = self.handler_queue.get
        with self:
            while True:
                event = handler_queue_get()
                event_type = event.EVENT_TYPE

                if event_type == MARKET_BOOK_EVENT:
                    self._process_market_books(event)

                elif event_type == CURRENT_ORDERS_EVENT:
                    self._process_current_orders(event)

                elif event_type == CUSTOM_EVENT_EVENT:
                    self._process_custom_event(event)

                elif event_type == SPORTS_DATA_EVENT:
                    self._process_sports_data(event)

                elif event_type == RAW_DATA_EVENT:
                    self._process_raw_data(event)

                elif event_type == MARKET_CATALOGUE_EVENT:
                    self._process_market_catalogues(event)

                elif event_type == CLEARED_MARKETS_EVENT:
                    self._process_cleared_markets(event)

                elif event_type == CLEARED_ORDERS_EVENT:
                    self._process_cleared_orders(event)

                elif event_type == CLOSE_MARKET_EVENT:
                    self._process_close_market(event)

                elif event_type == TERMINATOR_EVENT:
                    break

                else:
                    logger.error("Unknown item in handler_queue: %s" % str(event))

                del event

    def _add_default_workers(self):
        client_timeouts = [
            client.betting_client.session_timeout for client in self.clients
        ]
        ka_interval = min((min(client_timeouts) / 2), 1200)
        self.add_worker(
            worker.BackgroundWorker(
                self, function=worker.keep_alive, interval=ka_interval
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
        if not all([client.market_recording_mode for client in self.clients]):
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
                    function=worker.poll_market_closure,
                    interval=60,
                    start_delay=10,  # wait for login
                )
            )

    def __repr__(self) -> str:
        return "<Flumine>"

    def __str__(self) -> str:
        return "<Flumine>"
