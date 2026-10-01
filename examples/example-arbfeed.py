import os
import time
import logging
from pythonjsonlogger import jsonlogger

from flumine import Flumine, clients
from flumine.events.events import TerminationEvent
from flumine.worker import BackgroundWorker
from strategies.arbsignal import ArbSignalStrategy
from workers.arbfeed import poll_arb_feed
from workers.arbscanner import ArbScanner

"""
External signal feed polled by a flumine worker.

Runs offline by default: without X402_WALLET_KEY the scanner returns
bundled SAMPLE data (not real market data) and makes no network calls.
Setting X402_WALLET_KEY opts in to the paid live feed (x402, USDC on
Base, capped by max_usd_per_call per request, eth-account required).

    cd examples && python example-arbfeed.py

To gate real markets swap the SimulatedClient for a BetfairClient and
subscribe the strategy to a stream, see examples/tennisexample.py
"""

logger = logging.getLogger()

custom_format = "%(asctime) %(levelname) %(message)"
log_handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(custom_format)
formatter.converter = time.gmtime
log_handler.setFormatter(formatter)
logger.addHandler(log_handler)
logger.setLevel(logging.INFO)

scanner = ArbScanner(max_usd_per_call=0.02)
if scanner.demo:
    logger.info("Arb feed in demo mode, using SAMPLE data (no network calls)")
else:
    logger.warning("Arb feed in LIVE mode, each poll pays up to $0.02 USDC")

client = clients.SimulatedClient()
framework = Flumine(client=client)

strategy = ArbSignalStrategy(
    name="arbsignal",
    context={"min_net_yield_c": 1.0, "max_signal_age": 120},
)
framework.add_strategy(strategy)

framework.add_worker(
    BackgroundWorker(
        framework,
        poll_arb_feed,
        func_kwargs={"scanner": scanner, "limit": 10, "mode": "opportunities"},
        interval=60 if scanner.demo else int(os.environ.get("ARB_POLL_INTERVAL", 300)),
    )
)


def stop(context: dict, flumine) -> None:
    # demo only: terminate once the feed has been processed
    for s in flumine.strategies:
        for signal in s.active_signals():
            logger.info(
                "Active signal",
                extra={"pair": signal.get("event") or signal.get("pair")},
            )
    flumine.handler_queue.put(TerminationEvent(flumine))


framework.add_worker(BackgroundWorker(framework, stop, interval=None, start_delay=3))

framework.run()
