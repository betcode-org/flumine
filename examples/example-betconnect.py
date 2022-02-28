import time
import logging
import betconnect
import betfairlightweight
from betfairlightweight.filters import streaming_market_filter
from pythonjsonlogger import jsonlogger

from flumine import Flumine, clients, BaseStrategy

logger = logging.getLogger()

custom_format = "%(asctime) %(levelname) %(message)"
log_handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(custom_format)
formatter.converter = time.gmtime
log_handler.setFormatter(formatter)
logger.addHandler(log_handler)
logger.setLevel(logging.INFO)


class ExampleStrategy(BaseStrategy):
    def check_market_book(self, market, market_book):
        # process_market_book only executed if this returns True
        if market_book.status != "CLOSED":
            return True

    def process_market_book(self, market, market_book):
        print(market, market_book)


framework = Flumine()

# add clients
betfair_client = clients.BetfairClient(betfairlightweight.APIClient("username"))
framework.add_client(betfair_client)

betconnect_client = clients.BetConnectClient(betconnect.APIClient("username", "password", "apiKey", "ppURL"))
framework.add_client(betconnect_client)

strategy = ExampleStrategy(
    market_filter=streaming_market_filter(market_ids=["1.195310607"]),
)
framework.add_strategy(strategy)

framework.run()
