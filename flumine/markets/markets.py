from typing import Iterator, Optional

from .market import Market
from ..order.order import BetfairOrder


class Markets:
    def __init__(self):
        self._markets = {}  # marketId: <Market>

    def add_market(self, market_id: str, market: Market) -> None:
        if market_id in self._markets:
            self._markets[market_id].open_market()
        else:
            self._markets[market_id] = market

    def close_market(self, market_id: str) -> Market:
        market = self._markets[market_id]
        market.close_market()
        return market

    def remove_market(self, market_id: str) -> None:
        del self._markets[market_id].blotter
        del self._markets[market_id]

    def get_order(self, market_id: str, order_id: str) -> Optional[BetfairOrder]:
        try:
            return self.markets[market_id].blotter[order_id]
        except KeyError:
            return

    def get_order_from_bet_id(
        self, market_id: str, bet_id: str
    ) -> Optional[BetfairOrder]:
        blotter = self.markets[market_id].blotter
        lookup = {order.bet_id: order for order in blotter}
        try:
            return lookup[bet_id]
        except KeyError:
            return

    @property
    def markets(self) -> dict:
        return self._markets

    @property
    def open_market_ids(self) -> list:
        return [m.market_id for m in self if not m.closed]

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
