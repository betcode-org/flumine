import logging

from betfairlightweight.streaming.listener import StreamListener
from betfairlightweight.streaming.stream import BaseStream


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
            raise ValueError('Not expecting an order stream...')


class FlumineStream(BaseStream):

    def _process(self, market_books, publish_time):
        for market_book in market_books:
            market_id = market_book.get('id')
            if 'marketDefinition' in market_book and market_book['marketDefinition']['status'] == 'CLOSED':
                if market_id in self._caches:
                    # removes closed market from cache
                    logger.info('[MarketStream: %s] %s removed' % (self.unique_id, market_id))
                    del self._caches[market_id]
            elif self._caches.get(market_id) is None:
                # adds empty object to cache to track live market count
                logger.info('[MarketStream: %s] %s added' % (self.unique_id, market_id))
                self._caches[market_id] = object()

        self.output_queue(market_books, publish_time)
        self._updates_processed += len(market_books)

    def __str__(self):
        return 'FlumineStream'

    def __repr__(self):
        return '<FlumineStream [%s]>' % len(self._caches)
