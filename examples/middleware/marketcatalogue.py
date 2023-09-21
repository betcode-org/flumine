import json
from pathlib import Path

from betfairlightweight.resources import MarketCatalogue
from flumine.events.events import MarketCatalogueEvent
from flumine.markets.middleware import Middleware


MARKET_CATALOGUE_PATH = ""  # update to correct path


# Will read and parse the market_catalogue file and add to the market object when simulating
# Usage framework.add_market_middleware(MarketCatalogueMiddleware())
class MarketCatalogueMiddleware(Middleware):
    def add_market(self, market) -> None:
        catalogue_file_path = Path(MARKET_CATALOGUE_PATH) / market.market_id
        if catalogue_file_path.exists():
            market.flumine._process_market_catalogues(
                MarketCatalogueEvent(
                    [MarketCatalogue(**json.loads(catalogue_file_path.read_bytes()))]
                )
            )
