import logging
import time

import requests

from flumine.events.events import CustomEvent
from .arbscanner import ArbScanner, ArbScannerError, is_executable

logger = logging.getLogger(__name__)

"""
Worker polling an external signal feed (here a Kalshi <-> PredictIt
arbitrage scanner, see examples/workers/arbscanner.py) and passing
the result to the main thread via a CustomEvent, the callback then
stores the signals in each strategy context:

    framework.add_worker(
        BackgroundWorker(
            framework,
            poll_arb_feed,
            func_kwargs={"scanner": ArbScanner(), "q": "senate"},
            interval=60,
        )
    )

Without X402_WALLET_KEY the scanner returns bundled SAMPLE data and
makes no network calls, see examples/example-arbfeed.py
"""


def poll_arb_feed(
    context: dict,
    flumine,
    scanner: ArbScanner,
    q: str = None,
    limit: int = 10,
    mode: str = "opportunities",
) -> None:
    try:
        response = scanner.scan(q=q, limit=limit, mode=mode)
    except (ArbScannerError, requests.RequestException, ValueError) as e:
        logger.warning("poll_arb_feed error", extra={"error": str(e)})
        return
    context["polls"] = context.get("polls", 0) + 1
    flumine.handler_queue.put(CustomEvent(response, callback))


def callback(flumine, event):
    # executed on the main thread, safe to update strategy context
    response = event.event
    signals = response["opportunities"]
    logger.info(
        "Arb feed update: %s signals, %s executable%s",
        len(signals),
        len([s for s in signals if is_executable(s)]),
        " (SAMPLE DATA)" if response.get("sample_data") else "",
    )
    for strategy in flumine.strategies:
        strategy.context["arb_signals"] = signals
        strategy.context["arb_signals_updated"] = time.time()
