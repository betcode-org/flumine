import time
import threading
import logging
from typing import Callable, Optional
from betfairlightweight import BetfairError, filters, exceptions

from . import config
from .events import events
from .utils import chunks
from .clients import ExchangeType

logger = logging.getLogger(__name__)


class BackgroundWorker(threading.Thread):
    def __init__(
        self,
        flumine,
        function: Callable,
        interval: Optional[int],
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
        self._running = False

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
        self._running = True
        while self._running:
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
            if self.interval is None:
                break
            time.sleep(self.interval)

    def shutdown(self, timeout: int = 4) -> None:
        logger.info(
            "BackgroundWorker {0} shutting down".format(self.name),
            extra={
                "worker_name": self.name,
                "function": self.function,
            },
        )
        self._running = False
        self.join(timeout)


def keep_alive(context: dict, flumine) -> None:
    """Attempt keep alive if required or
    login if keep alive failed
    """
    for client in flumine.clients:
        if client.EXCHANGE == ExchangeType.BETFAIR:
            if client.betting_client.session_token:
                resp = client.keep_alive()
                if resp is None or resp.status == "SUCCESS":
                    continue
        elif client.EXCHANGE == ExchangeType.BETCONNECT:
            resp = client.keep_alive()
            if resp:
                continue
        # keep-alive failed lets try a login
        client.login()


def poll_market_catalogue(context: dict, flumine) -> None:
    # get betfair client
    client = flumine.clients.get_betfair_default()
    markets = [
        m.market_id
        for m in list(flumine.markets.markets.values())
        if m.update_market_catalogue and not m.closed
    ]
    for market_ids in chunks(markets, 25):
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
        except exceptions.StatusCodeError as e:
            # log as warning to prevent duplicate logs on betfair meltdown
            logger.warning(
                "poll_market_catalogue StatusCodeError",
                extra={"trading_function": "list_market_catalogue", "response": e},
                exc_info=True,
            )
            continue
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
    for client in flumine.clients:
        client.update_account_details()
        logger.info("Client update account details", extra=client.info)
        if client.account_funds:
            flumine.log_control(events.BalanceEvent(client))


def poll_market_closure(context: dict, flumine) -> None:
    markets = [
        market for market in list(flumine.markets.markets.values()) if market.closed
    ]
    for client in flumine.clients:
        if (
            client.EXCHANGE != ExchangeType.BETFAIR
            or client.paper_trade
            or client.market_recording_mode
        ):
            continue
        for market in markets:
            if client.username not in market.orders_cleared:
                if _get_cleared_orders(
                    flumine, client.betting_client, market.market_id
                ):
                    market.orders_cleared.append(client.username)
            if client.username not in market.market_cleared:
                if _get_cleared_market(
                    flumine, client.betting_client, market.market_id
                ):
                    market.market_cleared.append(client.username)


def _get_cleared_orders(flumine, betting_client, market_id: str) -> bool:
    from_record = 0
    while True:
        try:
            cleared_orders = betting_client.betting.list_cleared_orders(
                bet_status="SETTLED",
                from_record=from_record,
                market_ids=[market_id],
                customer_strategy_refs=[config.customer_strategy_ref],
            )
        except exceptions.StatusCodeError as e:
            # log as warning to prevent duplicate logs on betfair meltdown
            logger.warning(
                "_get_cleared_orders StatusCodeError",
                extra={"trading_function": "list_cleared_orders", "response": e},
                exc_info=True,
            )
            return False
        except BetfairError as e:
            logger.warning(
                "_get_cleared_orders error",
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
            customer_strategy_refs=[config.customer_strategy_ref],
            group_by="MARKET",
        )
    except exceptions.StatusCodeError as e:
        # log as warning to prevent duplicate logs on betfair meltdown
        logger.warning(
            "_get_cleared_market StatusCodeError",
            extra={"trading_function": "list_cleared_orders", "response": e},
            exc_info=True,
        )
        return False
    except BetfairError as e:
        logger.error(
            "_get_cleared_market error",
            extra={"trading_function": "list_cleared_orders", "response": e},
            exc_info=True,
        )
        return False

    if cleared_markets.orders:
        flumine.handler_queue.put(events.ClearedMarketsEvent(cleared_markets))
        return True
    else:
        return False
