from betfairlightweight.streaming.listener import StreamListener
from betfairlightweight.streaming.stream import BaseStream


"""
Custom listener that doesn't do any processing,
helps reduce CPU. Hacks the output queue with a
recorder to remove the need for a handler thread.
"""


class FlumineListener(StreamListener):

    def __init__(self, recorder, max_latency=0.5):
        super(FlumineListener, self).__init__(max_latency)
        self.recorder = recorder

    def _add_stream(self, unique_id, stream_type):
        if stream_type == 'marketSubscription':
            return FlumineStream(
                unique_id, self.recorder, self.max_latency, self.lightweight
            )
        elif stream_type == 'orderSubscription':
            raise ValueError('Not expecting an order stream...')


class FlumineStream(BaseStream):

    def _process(self, market_books, publish_time):
        self.output_queue({
            "op": "mcm",
            "clk": None,
            "pt": 0000000000,
            "mc": market_books
        })
        self._updates_processed += len(market_books)

    def __str__(self):
        return 'FlumineStream'

    def __repr__(self):
        return '<FlumineStream [%s]>' % len(self._caches)
