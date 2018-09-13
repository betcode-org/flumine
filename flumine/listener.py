import logging
from betfairlightweight.streaming.listener import StreamListener
from betfairlightweight.streaming.stream import BaseStream

from .exceptions import ListenerError


"""
Custom listener that doesn't do any processing,
helps reduce CPU. Hacks the output queue with a
recorder to remove the need for a handler thread.
"""

logger = logging.getLogger(__name__)


class FlumineListener(StreamListener):

    def __init__(self, recorder, max_latency=0.5):
        super(FlumineListener, self).__init__(recorder, max_latency)
        self.recorder = recorder

    def _add_stream(self, unique_id, stream_type):
        if stream_type == 'marketSubscription':
            return FlumineStream(self)
        elif stream_type == 'orderSubscription':
            raise ListenerError('Not expecting an order stream...')
        elif stream_type == 'raceSubscription':
            return FlumineRaceStream(self)


class FlumineStream(BaseStream):

    _lookup = 'mc'

    def _process(self, market_books, publish_time):
        for market_book in market_books:
            market_id = market_book.get('id')
            if 'marketDefinition' in market_book and market_book['marketDefinition']['status'] == 'CLOSED':
                if market_id in self._caches:
                    # removes closed market from cache
                    del self._caches[market_id]
                    logger.info('[MarketStream: %s] %s removed, %s markets in cache' %
                                (self.unique_id, market_id, len(self._caches)))
            elif self._caches.get(market_id) is None:
                # adds empty object to cache to track live market count
                self._caches[market_id] = object()
                logger.info('[MarketStream: %s] %s added, %s markets in cache' %
                            (self.unique_id, market_id, len(self._caches)))

        self.output_queue(market_books, publish_time)
        self._updates_processed += len(market_books)

    def __str__(self):
        return 'FlumineStream'

    def __repr__(self):
        return '<FlumineStream [%s]>' % len(self._caches)


class FlumineRaceStream(BaseStream):

    _lookup = 'rc'

    def _process(self, race_updates, publish_time):
        for update in race_updates:
            market_id = update['mid']
            if self._caches.get(market_id) is None:
                # adds empty object to cache to track live market count
                self._caches[market_id] = object()
                logger.info('[RaceStream: %s] %s added, %s markets in cache' %
                            (self.unique_id, market_id, len(self._caches)))

        self.output_queue(race_updates, publish_time)
        self._updates_processed += len(race_updates)

    def __str__(self):
        return 'FlumineRaceStream'

    def __repr__(self):
        return '<FlumineRaceStream [%s]>' % len(self._caches)
