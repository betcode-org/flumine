import time
import threading
import logging
import queue
from betfairlightweight import BetfairError, filters

from .event.event import MarketCatalogueEvent
from .utils import chunks

logger = logging.getLogger(__name__)


class BackgroundWorker(threading.Thread):
    def __init__(
        self,
        interval: int,
        function,
        func_args: tuple = None,
        func_kwargs: dict = None,
        start_delay: int = 0,
        **kwargs
    ):
        threading.Thread.__init__(self, daemon=True, **kwargs)
        self.interval = interval
        self.function = function
        self.func_args = func_args if func_args is not None else []
        self.func_kwargs = func_kwargs if func_kwargs is not None else {}
        self.start_delay = start_delay

    def run(self) -> None:
        time.sleep(self.start_delay)
        while self.is_alive():
            try:
                self.function(*self.func_args, **self.func_kwargs)
            except Exception as e:
                logger.error("Error in BackgroundWorker {0}: {1}".format(self.name, e))
            time.sleep(self.interval)


def keep_alive(client) -> None:
    logger.info("Trading client keep_alive worker executing", extra={"client": client})
    if client.betting_client.session_token is None:
        client.login()
    else:
        client.keep_alive()


def poll_market_catalogue(client, markets, handler_queue: queue.Queue) -> None:
    logger.info("Market Catalogue polling worker executing", extra={"client": client})
    live_markets = list(markets.markets.keys())
    for market_ids in chunks(live_markets, 100):
        try:
            market_catalogues = client.betting_client.betting.list_market_catalogue(
                filter=filters.market_filter(market_ids=market_ids),
                max_results=100,
                market_projection=[
                    "COMPETITION",
                    "EVENT",
                    "EVENT_TYPE",
                    "RUNNER_DESCRIPTION",
                    "RUNNER_METADATA",
                    "MARKET_START_TIME",
                    "MARKET_DESCRIPTION",
                ],
            )
        except BetfairError as e:
            logger.error(
                "poll_market_catalogue error",
                exc_info=True,
                extra={"trading_function": "list_market_catalogue", "response": e},
            )
            continue

        if market_catalogues:
            handler_queue.put(MarketCatalogueEvent(market_catalogues))
