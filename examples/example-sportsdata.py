import time
import logging
import betfairlightweight
from betfairlightweight.filters import streaming_market_filter
from pythonjsonlogger import jsonlogger

from flumine import Flumine, clients, BaseStrategy
from flumine.streams.marketstream import MarketStream
from flumine.streams.sportsdatastream import SportsDataStream

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

# create stream(s) (market data)
market_stream = MarketStream(
    framework,
    market_filter=streaming_market_filter(
        event_type_ids=["4"], market_types=["MATCH_ODDS"]
    ),
)
framework.add_stream(market_stream)

# create stream(s) (sports data)
sports_data_stream = SportsDataStream(
    framework,
    sports_data_filter="cricketSubscription",  # "cricketSubscription" or "raceSubscription"
)
framework.add_stream(sports_data_stream)

strategy = ExampleStrategy(streams=[market_stream, sports_data_stream])
framework.add_strategy(strategy)

framework.run()
