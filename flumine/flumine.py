import logging

from .baseflumine import BaseFlumine
from .event.event import EventType
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
                if event == EventType.TERMINATOR:
                    self._process_end_flumine()
                    break

                elif event.EVENT_TYPE == EventType.MARKET_CATALOGUE:
                    self._process_market_catalogues(event)

                elif event.EVENT_TYPE == EventType.MARKET_BOOK:
                    self._process_market_books(event)

                elif event.EVENT_TYPE == EventType.RAW_DATA:
                    self._process_raw_data(event)

                elif event.EVENT_TYPE == EventType.CURRENT_ORDERS:
                    logger.info(event)

                elif event.EVENT_TYPE == EventType.CLEARED_MARKETS:
                    logger.info(event)

                elif event.EVENT_TYPE == EventType.CLEARED_ORDERS:
                    logger.info(event)

                elif event.EVENT_TYPE == EventType.CLOSE_MARKET:
                    logger.info(event)

                elif event.EVENT_TYPE == EventType.STRATEGY_RESET:
                    logger.info(event)

                elif event.EVENT_TYPE == EventType.CUSTOM_EVENT:
                    logger.info(event)

                elif event.EVENT_TYPE == EventType.NEW_DAY:
                    logger.info(event)

                else:
                    logger.error("Unknown item in handler_queue: %s" % str(event))

    def _add_default_workers(self):
        self.add_worker(
            worker.BackgroundWorker(
                interval=1200,
                function=worker.keep_alive,
                name="keep_alive",
                func_args=(self.client,),
            )
        )
        self.add_worker(
            worker.BackgroundWorker(
                start_delay=5,  # wait for streams to populate
                interval=60,
                function=worker.poll_market_catalogue,
                name="poll_market_catalogue",
                func_args=(self.client, self.markets, self.handler_queue),
            )
        )

    def __repr__(self) -> str:
        return "<Flumine>"

    def __str__(self) -> str:
        return "<Flumine [%s]>" % self.status
