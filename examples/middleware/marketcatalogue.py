import json
from pathlib import Path

from betfairlightweight.resources import MarketCatalogue
from flumine.events.events import MarketCatalogueEvent
from flumine.markets.middleware import Middleware


class MarketCatalogueMiddleware(Middleware):
    """
    Will read and parse the market_catalogue file and add to the market object when simulating.
    Usage: framework.add_market_middleware(MarketCatalogueMiddleware(market_catalogue_dir))
    """

    def __init__(self, market_catalogue_dir: str):
        self.market_catalogue_dir = Path(market_catalogue_dir)

    def add_market(self, market) -> None:
        catalogue_file_path = self.market_catalogue_dir / (market.market_id + ".json")
        if catalogue_file_path.exists():
            market.flumine._process_market_catalogues(
                MarketCatalogueEvent(
                    [MarketCatalogue(**json.loads(catalogue_file_path.read_bytes()))]
                )
            )
