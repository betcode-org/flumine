from typing import Iterator

from .market import Market


class Markets:
    def __init__(self):
        self._markets = {}  # marketId: <Market>

    def add_market(self, market_id: str, live_market: Market) -> None:
        if market_id in self._markets:
            self._markets[market_id].open_market()
        else:
            self._markets[market_id] = live_market

    def close_market(self, market_id: str) -> Market:
        live_market = self._markets[market_id]
        live_market.close_market()
        return live_market

    @property
    def markets(self) -> dict:
        return {
            key: value for key, value in self._markets.items() if value.closed is False
        }

    def __iter__(self) -> Iterator[Market]:
        return iter(self.markets)

    def __len__(self) -> int:
        return len(self.markets)
