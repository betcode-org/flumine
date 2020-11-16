import logging
import queue
from threading import Thread

from ..events import events
from ..events.events import EventType

logger = logging.getLogger(__name__)


class LoggingControl(Thread):
    """
    Base Logging Control instance, used to output logging of
    trades, orders, new markets and market closure. Can be
    used to send data to a database or API for further analysis.
    """

    # todo handle/store errors for retry

    NAME = "LOGGING_CONTROL"

    def __init__(self, daemon: bool = True):
        Thread.__init__(self, daemon=daemon, name=self.NAME)
        self.logging_queue = queue.Queue()
        self.cache = []

    def run(self) -> None:
        logger.info("Starting logging control %s" % self.NAME)
        while True:
            event = self.logging_queue.get()
            if event is None:
                logger.info("Shutting down logging control %s" % self.NAME)
                break
            else:
                try:
                    self.process_event(event)
                except Exception as e:
                    logger.critical(
                        "{0} exception raised in {0}".format(e, self.NAME),
                        exc_info=True,
                        extra={"event": event},
                    )

    def process_event(self, event: events.BaseEvent):
        if event.EVENT_TYPE == EventType.CONFIG:
            self._process_config(event)

        elif event.EVENT_TYPE == EventType.STRATEGY:
            self._process_strategy(event)

        elif event.EVENT_TYPE == EventType.MARKET:
            self._process_market(event)

        elif event.EVENT_TYPE == EventType.TRADE:
            self._process_trade(event)

        elif event.EVENT_TYPE == EventType.ORDER:
            self._process_order(event)

        elif event.EVENT_TYPE == EventType.BALANCE:
            self._process_balance(event)

        elif event.EVENT_TYPE == EventType.CLEARED_ORDERS:
            self._process_cleared_orders(event)

        elif event.EVENT_TYPE == EventType.CLEARED_ORDERS_META:
            self._process_cleared_orders_meta(event)

        elif event.EVENT_TYPE == EventType.CLEARED_MARKETS:
            self._process_cleared_markets(event)

        elif event.EVENT_TYPE == EventType.CLOSE_MARKET:
            self._process_closed_market(event)

        elif event.EVENT_TYPE == EventType.CUSTOM_EVENT:
            self._process_custom_event(event)

        elif event.EVENT_TYPE == EventType.NEW_DAY:
            self._process_new_day(event)

        elif event.EVENT_TYPE == EventType.TERMINATOR:
            self._process_end_flumine(event)
            self.logging_queue.put(None)

        else:
            logger.error("Unwanted item in logging control: {0}".format(event))

    def _process_config(self, event):
        logger.debug("process_config: %s" % event)

    def _process_strategy(self, event):
        logger.debug("process_strategy: %s" % event)

    def _process_market(self, event):
        logger.debug("process_market: %s" % event)

    def _process_trade(self, event):
        logger.debug("process_trade: %s" % event)

    def _process_order(self, event):
        logger.debug("process_order: %s" % event)

    def _process_balance(self, event):
        logger.debug("process_balance: %s" % event)

    def _process_cleared_orders(self, event):
        logger.debug("process_cleared_orders: %s" % event)

    def _process_cleared_orders_meta(self, event):
        logger.debug("process_cleared_orders_meta: %s" % event)

    def _process_cleared_markets(self, event):
        logger.debug("process_cleared_markets: %s" % event)

    def _process_closed_market(self, event):
        logger.debug("process_closed_market: %s" % event)

    def _process_custom_event(self, event):
        logger.debug("process_custom_event: %s" % event)

    def _process_new_day(self, event):
        logger.debug("process_new_day: %s" % event)

    def _process_end_flumine(self, event):
        logger.debug("_process_end_flumine: %s" % event)
