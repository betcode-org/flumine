import logging
import datetime

from ..baseflumine import BaseFlumine
from ..event.event import MarketBookEvent
from .. import config

logger = logging.getLogger(__name__)


class FlumineBacktest(BaseFlumine):
    """
    Single threaded implementation of flumine
    for backtesting strategies with betfair
    historic (or self recorded) streaming data.
    """

    BACKTEST = True

    def run(self) -> None:
        with self:
            self._monkey_patch_datetime()

            for stream in self.streams:
                stream_gen = stream.create_generator()

                logger.info(
                    "Starting historical market '{0}'".format(stream.market_filter)
                )

                for event in stream_gen():
                    for market_book in event:
                        config.current_time = market_book.publish_time
                        market_book.streaming_unique_id = stream.stream_id
                    self._process_market_books(MarketBookEvent(event))

                logger.info(
                    "Completed historical market '{0}'".format(stream.market_filter)
                )

            self._process_end_flumine()

            logger.info("Backtesting complete")

            self._unpatch_datetime()

    # def _process_market_books(self, event):
    #     for market_book in event.event:
    #         for strategy in self.strategies:
    #             if strategy.check_market(market_book):
    #                 strategy.process_market_book(market_book)

    def _monkey_patch_datetime(self):
        config.current_time = datetime.datetime.utcnow()

        class NewDateTime(datetime.datetime):
            @classmethod
            def utcnow(cls):
                return config.current_time

        self._old_datetime = datetime.datetime
        datetime.datetime = NewDateTime

    def _unpatch_datetime(self):
        datetime.datetime = self._old_datetime

    def __repr__(self) -> str:
        return "<FlumineBacktest>"

    def __str__(self) -> str:
        return "<FlumineBacktest [%s]>" % self.status
