import logging
import datetime

from betfairlightweight.streaming.listener import StreamListener
from betfairlightweight.streaming.stream import BaseStream
from betfairlightweight.streaming.cache import MarketBookCache
from betfairlightweight.resources.baseresource import BaseResource

from ..events.events import MarketBookEvent

logger = logging.getLogger(__name__)


class HistoricListener(StreamListener):
    def __init__(self, inplay=None, seconds_to_start=None, **kwargs):
        super(HistoricListener, self).__init__(**kwargs)
        self.inplay = inplay
        self.seconds_to_start = seconds_to_start

    def _add_stream(self, unique_id, stream_type):
        if stream_type == "marketSubscription":
            return Stream(self)


class Stream(BaseStream):

    _lookup = "mc"

    def _process(self, market_books, publish_time):
        for market_book in market_books:
            market_id = market_book["id"]
            market_book_cache = self._caches.get(market_id)

            if (
                market_book.get("img") or market_book_cache is None
            ):  # historic data does not contain img
                market_book_cache = MarketBookCache(
                    publish_time=publish_time, **market_book
                )
                self._caches[market_id] = market_book_cache
                logger.info("[MarketStream: %s] %s added" % (self.unique_id, market_id))
            else:
                market_book_cache.update_cache(market_book, publish_time)
                self._updates_processed += 1

    def snap(self, market_ids=None):
        market_books = []

        for cache in list(self._caches.values()):
            if market_ids and cache.market_id not in market_ids:
                continue
            # if market has closed send regardless
            if cache.market_definition["status"] != "CLOSED":
                if self._listener.inplay:
                    if not cache.market_definition["inPlay"]:
                        continue

                elif self._listener.seconds_to_start:
                    _now = datetime.datetime.utcfromtimestamp(cache.publish_time / 1e3)
                    _market_time = BaseResource.strip_datetime(
                        cache.market_definition["marketTime"]
                    )
                    seconds_to_start = (_market_time - _now).total_seconds()
                    if seconds_to_start > self._listener.seconds_to_start:
                        continue

                if self._listener.inplay is False:
                    if cache.market_definition["inPlay"]:
                        continue

            market_books.append(
                cache.create_resource(self.unique_id, None, self._lightweight)
            )
        if market_books:
            return market_books
