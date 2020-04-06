import logging

from ..baseflumine import BaseFlumine
from ..event.event import MarketBookEvent

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
            # todo monkeypatch datetime

            for stream in self.streams:
                stream_gen = stream.create_generator()

                logger.info(
                    "Starting historical market '{0}'".format(stream.market_filter)
                )

                for event in stream_gen():
                    for market_book in event:
                        market_book.streaming_unique_id = stream.stream_id
                    self._process_market_books(MarketBookEvent(event))

                logger.info(
                    "Completed historical market '{0}'".format(stream.market_filter)
                )

            self._process_end_flumine()

            logger.info("Backtesting complete")

            # todo un monkeypatch datetime

    # def _process_market_books(self, event):
    #     for market_book in event.event:
    #         for strategy in self.strategies:
    #             if strategy.check_market(market_book):
    #                 strategy.process_market_book(market_book)

    def __repr__(self) -> str:
        return "<FlumineBacktest>"

    def __str__(self) -> str:
        return "<FlumineBacktest [%s]>" % self.status
