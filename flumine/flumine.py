import logging

from .baseflumine import BaseFlumine
from .event.event import Event

logger = logging.getLogger(__name__)


class Flumine(BaseFlumine):
    def run(self) -> None:
        """
        Main run thread
        """
        with self:
            while True:
                event = self.handler_queue.get()
                if event == Event.TERMINATOR:
                    break

                elif event.EVENT == Event.MARKET_CATALOGUE:
                    print(event)

                elif event.EVENT == Event.MARKET_BOOK:
                    print(event)

                elif event.EVENT == Event.CURRENT_ORDERS:
                    print(event)

                elif event.EVENT == Event.CLEARED_MARKETS:
                    print(event)

                elif event.EVENT == Event.CLEARED_ORDERS:
                    print(event)

                elif event.EVENT == Event.CLOSE_MARKET:
                    print(event)

                elif event.EVENT == Event.STRATEGY_RESET:
                    print(event)

                elif event.EVENT == Event.CUSTOM_EVENT:
                    print(event)

                elif event.EVENT == Event.NEW_DAY:
                    print(event)

                else:
                    logger.error("Unknown item in handler_queue: %s" % str(event))

    def __repr__(self) -> str:
        return "<Flumine>"

    def __str__(self) -> str:
        return "<Flumine [%s]>" % self.status
