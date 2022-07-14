import logging
from typing import Iterator, Optional
from collections import defaultdict

from .market import Market
from ..order.order import BetfairOrder

logger = logging.getLogger(__name__)


class Markets:
    def __init__(self):
        self._markets = {}  # marketId: <Market>
        self.events = defaultdict(list)  # eventId: [<Market>, ]

    def add_market(self, market_id: str, market: Market) -> None:
        if market_id in self._markets:
            self._markets[market_id].open_market()
        else:
            self._markets[market_id] = market
            if market.event_id:
                self.events[market.event_id].append(market)

    def close_market(self, market_id: str) -> Market:
        market = self._markets[market_id]
        market.close_market()
        return market

    def remove_market(self, market_id: str) -> None:
        market = self._markets[market_id]
        del self._markets[market_id]
        event_id = market.event_id
        if event_id in self.events:
            if market in self.events[event_id]:
                self.events[event_id].remove(market)
        del market.blotter
        del market
        logger.info(
            "Market removed",
            extra={"market_id": market_id, "event_id": event_id, "events": self.events},
        )

    def get_order(self, market_id: str, order_id: str) -> Optional[BetfairOrder]:
        try:
            return self.markets[market_id].blotter[order_id]
        except KeyError:
            return

    def get_order_from_bet_id(
        self, market_id: str, bet_id: str
    ) -> Optional[BetfairOrder]:
        blotter = self.markets[market_id].blotter
        return blotter.get_order_bet_id(bet_id)

    @property
    def markets(self) -> dict:
        return self._markets

    @property
    def open_market_ids(self) -> list:
        return [m.market_id for m in self if m.status == "OPEN"]

    @property
    def live_orders(self) -> bool:
        for market in self:
            if market.closed is False and market.blotter.has_live_orders:
                return True
        return False

    def __iter__(self) -> Iterator[Market]:
        return iter(list(self.markets.values()))

    def __len__(self) -> int:
        return len(self.markets)
