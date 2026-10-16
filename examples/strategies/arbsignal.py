import logging
import time

from flumine import BaseStrategy

logger = logging.getLogger(__name__)


class ArbSignalStrategy(BaseStrategy):
    """
    Example strategy gated on an external signal feed, signals
    are stored in context["arb_signals"] by the callback in
    examples/workers/arbfeed.py
    - Only processes OPEN markets whilst a fresh executable
      signal >= context["min_net_yield_c"] exists
    - Logs each new signal, no orders are placed
    """

    def check_market_book(self, market, market_book):
        if market_book.status == "OPEN" and self.active_signals():
            return True

    def process_market_book(self, market, market_book):
        seen = market.context.setdefault("arb_signals_seen", set())
        for signal in self.active_signals():
            key = _label(signal)
            if key not in seen:
                seen.add(key)
                logger.info(
                    "Arb signal active",
                    extra={
                        "market_id": market.market_id,
                        "pair": key,
                        "net_yield_c": _net_yield_c(signal),
                    },
                )

    def active_signals(self) -> list:
        updated = self.context.get("arb_signals_updated")
        max_age = self.context.get("max_signal_age", 120)
        if updated is None or time.time() - updated > max_age:
            return []
        min_yield = self.context.get("min_net_yield_c", 1.0)
        return [
            s
            for s in self.context.get("arb_signals", [])
            if _label(s)
            and s.get("executable") is True
            and _net_yield_c(s) >= min_yield
        ]


def _label(signal: dict) -> str:
    # live feed rows carry "event", older rows "pair", rows with neither are skipped
    return str(signal.get("event") or signal.get("pair") or "").strip()


def _net_yield_c(signal: dict) -> float:
    # tolerate missing fields, feed schema is not guaranteed
    try:
        return float(signal["best_direction"]["net_yield_c"])
    except (KeyError, TypeError, ValueError):
        return 0.0
