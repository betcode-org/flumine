import time
import threading
import logging
import queue
from betfairlightweight import BetfairError, filters

from . import config
from .events import events
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
        logger.info(
            "BackgroundWorker {0} starting".format(self.name),
            extra={"name": self.name, "function": self.function},
        )
        while self.is_alive():
            logger.debug(
                "BackgroundWorker {0} executing".format(self.name),
                extra={"name": self.name, "function": self.function},
            )
            try:
                self.function(*self.func_args, **self.func_kwargs)
            except Exception as e:
                logger.error(
                    "Error in BackgroundWorker {0}: {1}".format(self.name, e),
                    extra={"worker_name": self.name, "function": self.function},
                )
            time.sleep(self.interval)


def keep_alive(client) -> None:
    """ Attempt keep alive if required or
    login if keep alive failed
    """
    if client.betting_client.session_token:
        try:
            resp = client.keep_alive()
            if resp is None or resp.status == "SUCCESS":
                return
        except BetfairError as e:
            logger.error(
                "keep_alive error",
                exc_info=True,
                extra={"trading_function": "keep_alive", "response": e},
            )
    # attempt login
    try:
        client.login()
    except BetfairError as e:
        logger.error(
            "login error",
            exc_info=True,
            extra={"trading_function": "login", "response": e},
        )


def poll_market_catalogue(client, markets, handler_queue: queue.Queue) -> None:
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
            handler_queue.put(events.MarketCatalogueEvent(market_catalogues))


def poll_account_balance(flumine, client) -> None:
    client.update_account_details()
    if client.account_funds:
        flumine.log_control(events.BalanceEvent(client.account_funds))


def poll_cleared_orders(flumine, client) -> None:
    while True:
        market_id = flumine.cleared_market_queue.get()
        from_record = 0
        while True:
            try:
                cleared_orders = client.betting_client.betting.list_cleared_orders(
                    bet_status="SETTLED",
                    from_record=from_record,
                    market_ids=[market_id],
                    customer_strategy_refs=[config.hostname],
                )
            except BetfairError as e:
                logger.error(
                    "poll_cleared_orders error",
                    extra={"trading_function": "list_cleared_orders", "response": e},
                    exc_info=True,
                )
                flumine.cleared_market_queue.put(market_id)  # try again
                break

            logger.info(
                "{0}: {1} cleared orders found, more available: {2}".format(
                    market_id, len(cleared_orders.orders), cleared_orders.more_available
                )
            )
            cleared_orders.market_id = market_id
            flumine.handler_queue.put(events.ClearedOrdersEvent(cleared_orders))
            flumine.log_control(events.ClearedOrdersEvent(cleared_orders))

            from_record += len(cleared_orders.orders)
            if not cleared_orders.more_available:
                break
