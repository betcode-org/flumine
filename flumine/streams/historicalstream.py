import logging
import datetime
from betfairlightweight.streaming import StreamListener, HistoricalGeneratorStream
from betfairlightweight.streaming.stream import BaseStream as BFLWBaseStream
from betfairlightweight.streaming.cache import MarketBookCache
from betfairlightweight.resources.baseresource import BaseResource

from .basestream import BaseStream

logger = logging.getLogger(__name__)


class Stream(BFLWBaseStream):
    """
    Custom bflw stream to speed up processing
    by limiting to inplay/not inplay or limited
    seconds to start.
    """

    _lookup = "mc"

    def _process(self, data: list, publish_time: int) -> None:
        for market_book in data:
            market_id = market_book["id"]
            market_book_cache = self._caches.get(market_id)
            if (
                market_book.get("img") or market_book_cache is None
            ):  # historic data does not contain img
                if "marketDefinition" not in market_book:
                    logger.error(
                        "[MarketStream: %s] Unable to add %s to cache due to marketDefinition "
                        "not being present (make sure EX_MARKET_DEF is requested)"
                        % (self.unique_id, market_id)
                    )
                    continue
                market_book_cache = MarketBookCache(
                    publish_time=publish_time, **market_book
                )
                self._caches[market_id] = market_book_cache
                logger.info(
                    "[MarketStream: %s] %s added, %s markets in cache"
                    % (self.unique_id, market_id, len(self._caches))
                )
            else:
                market_book_cache.update_cache(market_book, publish_time)
                self._updates_processed += 1

    def snap(self, market_ids: list = None) -> list:
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
                cache.create_resource(self.unique_id, self._lightweight)
            )
        return market_books


class HistoricListener(StreamListener):
    """
    Custom listener to restrict processing by
    inplay or seconds_to_start.
    """

    def __init__(self, inplay: bool = None, seconds_to_start: float = None, **kwargs):
        super(HistoricListener, self).__init__(**kwargs)
        self.inplay = inplay
        self.seconds_to_start = seconds_to_start

    def _add_stream(self, unique_id, stream_type):
        if stream_type == "marketSubscription":
            return Stream(self)


class HistoricalStream(BaseStream):

    LISTENER = HistoricListener
    MAX_LATENCY = None

    def run(self) -> None:
        pass

    def handle_output(self) -> None:
        pass

    def create_generator(self):
        stream = HistoricalGeneratorStream(
            file_path=self.market_filter,
            listener=self._listener,
            operation=self.operation,
        )
        return stream.get_generator()
