import json
import os

from betfairlightweight.resources import MarketCatalogue
from flumine.markets.middleware import Middleware

MARKET_CATALOGUE_PATH = ""  # update to correct path


# Will read and parse the market_catalogue file and add to the market object when backtesting
# Usage framework.add_middleware(MarketCatalogueMiddleware())
class MarketCatalogueMiddleware(Middleware):
    def __call__(self, market) -> None:
        pass

    def add_market(self, market) -> None:
        catalogue_file_path = os.path.join(MARKET_CATALOGUE_PATH, market.market_id)
        if os.path.exists(catalogue_file_path):
            with open(catalogue_file_path, "r") as r:
                data = r.read()
                catalogue_json_data = json.loads(data)
                market.market_catalogue = MarketCatalogue(**catalogue_json_data)
