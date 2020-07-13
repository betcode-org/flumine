import time
import threading
import logging
from typing import Callable
from betfairlightweight import BetfairError, filters

from . import config
from .events import events
from .utils import chunks

logger = logging.getLogger(__name__)


class BackgroundWorker(threading.Thread):
    def __init__(
        self,
        flumine,
        function: Callable,
        interval: int,
        func_args: tuple = None,
        func_kwargs: dict = None,
        start_delay: int = 0,
        context: dict = None,
        name: str = None,
        **kwargs
    ):
        name = name or function.__name__
        threading.Thread.__init__(self, daemon=True, name=name, **kwargs)
        self.flumine = flumine
        self.function = function
        self.interval = interval
        self.func_args = func_args if func_args is not None else []
        self.func_kwargs = func_kwargs if func_kwargs is not None else {}
        self.start_delay = start_delay
        self.context = context or {}

    def run(self) -> None:
        logger.info(
            "BackgroundWorker {0} starting".format(self.name),
            extra={
                "worker_name": self.name,
                "function": self.function,
                "context": self.context,
                "start_delay": self.start_delay,
                "interval": self.interval,
                "func_args": self.func_args,
                "func_kwargs": self.func_kwargs,
            },
        )
        time.sleep(self.start_delay)
        while self.is_alive():
            logger.debug(
                "BackgroundWorker {0} executing".format(self.name),
                extra={
                    "worker_name": self.name,
                    "function": self.function,
                    "context": self.context,
                },
            )
            try:
                self.function(
                    self.context, self.flumine, *self.func_args, **self.func_kwargs
                )
            except Exception as e:
                logger.error(
                    "Error in BackgroundWorker {0}: {1}".format(self.name, e),
                    extra={
                        "worker_name": self.name,
                        "function": self.function,
                        "context": self.context,
                    },
                    exc_info=True,
                )
            time.sleep(self.interval)


def keep_alive(context: dict, flumine) -> None:
    """ Attempt keep alive if required or
    login if keep alive failed
    """
    client = flumine.client
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


def poll_market_catalogue(context: dict, flumine) -> None:
    client = flumine.client
    live_markets = list(flumine.markets.markets.keys())
    for market_ids in chunks(live_markets, 25):
        try:
            market_catalogues = client.betting_client.betting.list_market_catalogue(
                filter=filters.market_filter(market_ids=market_ids),
                max_results=25,
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
            flumine.handler_queue.put(events.MarketCatalogueEvent(market_catalogues))


def poll_account_balance(context: dict, flumine) -> None:
    client = flumine.client
    client.update_account_details()
    if client.account_funds:
        flumine.log_control(events.BalanceEvent(client))


def poll_cleared_orders(context: dict, flumine) -> None:
    client = flumine.client
    processed_orders, processed_markets, market_cache = [], [], []
    while True:
        market_id = flumine.cleared_market_queue.get()
        if market_id not in processed_orders:
            if _get_cleared_orders(flumine, client.betting_client, market_id):
                processed_orders.append(market_id)
            else:
                time.sleep(10)
                flumine.cleared_market_queue.put(market_id)  # try again

        if market_id not in processed_markets:
            time.sleep(32)  # takes ~30s for orders to be aggregated to market level
            if _get_cleared_market(flumine, client.betting_client, market_id):
                processed_markets.append(market_id)
            else:
                if market_cache.count(market_id) > 7:  # give up after 7 attempts
                    market_cache = [m for m in market_cache if m != market_id]
                else:
                    market_cache.append(market_id)
                    flumine.cleared_market_queue.put(market_id)  # try again


def _get_cleared_orders(flumine, betting_client, market_id: str) -> bool:
    from_record = 0
    while True:
        try:
            cleared_orders = betting_client.betting.list_cleared_orders(
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
            return False

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
    return True


def _get_cleared_market(flumine, betting_client, market_id: str) -> bool:
    try:
        cleared_markets = betting_client.betting.list_cleared_orders(
            bet_status="SETTLED",
            market_ids=[market_id],
            customer_strategy_refs=[config.hostname],
            group_by="MARKET",
        )
    except BetfairError as e:
        logger.error(
            "_get_cleared_markets error",
            extra={"trading_function": "list_cleared_orders", "response": e},
            exc_info=True,
        )
        return False

    if cleared_markets.orders:
        flumine.handler_queue.put(events.ClearedMarketsEvent(cleared_markets))
        flumine.log_control(events.ClearedMarketsEvent(cleared_markets))
        return True
    else:
        return False
