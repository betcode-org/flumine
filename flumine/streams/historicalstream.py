import logging
import datetime
from typing import Optional
from betfairlightweight.streaming import StreamListener, HistoricalGeneratorStream
from betfairlightweight.streaming.stream import MarketStream, RaceStream
from betfairlightweight.streaming.cache import MarketBookCache, RaceCache
from betfairlightweight.resources.baseresource import BaseResource
from betfairlightweight.compat import json

from .basestream import BaseStream
from ..exceptions import ListenerError

logger = logging.getLogger(__name__)


class FlumineMarketStream(MarketStream):
    """
    Custom bflw stream to speed up processing
    by limiting to inplay/not inplay or limited
    seconds to start.
    `_process` updated to not call `on_process`
    which reduces some function calls.
    """

    def _process(self, data: list, publish_time: int) -> bool:
        for market_book in data:
            market_id = market_book["id"]
            full_image = market_book.get("img", False)
            market_book_cache = self._caches.get(market_id)

            if (
                full_image or market_book_cache is None
            ):  # historic data does not contain img
                if "marketDefinition" not in market_book:
                    logger.warning(
                        "[%s: %s]: Missing marketDefinition on market %s resulting "
                        "in potential missing data in the MarketBook (make sure "
                        "EX_MARKET_DEF is requested)"
                        % (self, self.unique_id, market_id)
                    )
                market_book_cache = MarketBookCache(
                    market_id, publish_time, self._lightweight
                )
                self._caches[market_id] = market_book_cache
                logger.info(
                    "[%s: %s]: %s added, %s markets in cache"
                    % (self, self.unique_id, market_id, len(self._caches))
                )

            market_book_cache.update_cache(market_book, publish_time)
            self._updates_processed += 1
        return False

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
            market_books.append(cache.create_resource(self.unique_id, snap=True))
        return market_books


class FlumineRaceStream(RaceStream):
    """
    `_process` updated to not call `on_process`
    which reduces some function calls.
    # todo snap optimisation?
    """

    def _process(self, race_updates: list, publish_time: int) -> bool:
        for update in race_updates:
            market_id = update["mid"]
            race_cache = self._caches.get(market_id)
            if race_cache is None:
                race_id = update.get("id")
                race_cache = RaceCache(
                    market_id, publish_time, race_id, self._lightweight
                )
                self._caches[market_id] = race_cache
                logger.info(
                    "[%s: %s]: %s added, %s markets in cache"
                    % (self, self.unique_id, market_id, len(self._caches))
                )
            race_cache.update_cache(update, publish_time)
            self._updates_processed += 1
        return False


class HistoricListener(StreamListener):
    """
    Custom listener to restrict processing by
    inplay or seconds_to_start.
    """

    def __init__(self, inplay: bool = None, seconds_to_start: float = None, **kwargs):
        super(HistoricListener, self).__init__(**kwargs)
        self.inplay = inplay
        self.seconds_to_start = seconds_to_start

    def _add_stream(self, unique_id: int, operation: str):
        if operation == "marketSubscription":
            return FlumineMarketStream(self, unique_id)
        elif operation == "orderSubscription":
            raise ListenerError("Unable to process order stream")
        elif operation == "raceSubscription":
            return FlumineRaceStream(self, unique_id)

    def on_data(self, raw_data: str) -> Optional[bool]:
        try:
            data = json.loads(raw_data)
        except ValueError:
            logger.error("value error: %s" % raw_data)
            return

        # remove error handler / operation check

        # skip on_change as we know it is always an update
        self.stream.on_update(data)


class HistoricalStream(BaseStream):

    LISTENER = HistoricListener
    MAX_LATENCY = None

    def run(self) -> None:
        pass

    def handle_output(self) -> None:
        pass

    def create_generator(self):
        self._listener.debug = False  # prevent logging calls on each update (slow)
        self._listener.update_clk = (
            False  # do not update clk on updates (not required when backtesting)
        )
        stream = HistoricalGeneratorStream(
            file_path=self.market_filter,
            listener=self._listener,
            operation=self.operation,
            unique_id=self.stream_id,
        )
        return stream.get_generator()
