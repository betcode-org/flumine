import logging
import datetime
from flumine.events.events import TerminationEvent

logger = logging.getLogger(__name__)

"""
Worker can be used as followed:

    framework.add_worker(
        BackgroundWorker(
            framework,
            terminate,
            func_kwargs={"today_only": True, "seconds_closed": 1200},
            interval=60,
            start_delay=60,
        )
    )

This will run every 60s and will terminate 
the framework if all markets starting 'today' 
have been closed for at least 1200s
"""


def terminate(
    context: dict, flumine, today_only: bool = True, seconds_closed: int = 600
) -> None:
    """terminate framework if no markets
    live today.
    """
    markets = list(flumine.markets.markets.values())
    markets_today = [
        m
        for m in markets
        if m.market_start_datetime.date()
        == datetime.datetime.now(datetime.timezone.utc).date()
        and (
            m.elapsed_seconds_closed is None
            or (m.elapsed_seconds_closed and m.elapsed_seconds_closed < seconds_closed)
        )
    ]
    if today_only:
        market_count = len(markets_today)
    else:
        market_count = len(markets)
    if market_count == 0:
        logger.info("No more markets available, terminating framework")
        flumine.handler_queue.put(TerminationEvent(flumine))
