import time
import logging
import betfairlightweight
from betfairlightweight.filters import streaming_market_filter
from pythonjsonlogger import jsonlogger

from flumine import Flumine, clients, BaseStrategy
from flumine.order.trade import Trade
from flumine.order.ordertype import LimitOrder
from flumine.order.order import OrderStatus

logger = logging.getLogger()

custom_format = "%(asctime) %(levelname) %(message)"
log_handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(custom_format)
formatter.converter = time.gmtime
log_handler.setFormatter(formatter)
logger.addHandler(log_handler)
logger.setLevel(logging.INFO)


class ExampleStrategy(BaseStrategy):
    def process_sports_data(self, market, sports_data) -> None:
        # called on each update from sports-data-stream
        print(market, sports_data)


trading = betfairlightweight.APIClient("username")
client = clients.BetfairClient(trading)

framework = Flumine(client)

strategy = ExampleStrategy(
    market_filter=streaming_market_filter(
        event_type_ids=["4"], market_types=["MATCH_ODDS"]
    ),
    sports_data_filter=[
        "cricketSubscription"
    ],  # "cricketSubscription" and/or "raceSubscription"
)
framework.add_strategy(strategy)

framework.run()
