import time
import logging
from pythonjsonlogger import jsonlogger

from flumine import FlumineBacktest, clients, BaseStrategy
from flumine.streams.historicalstream import HistoricalStream

logger = logging.getLogger()

custom_format = "%(asctime) %(levelname) %(message)"
log_handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(custom_format)
formatter.converter = time.gmtime
log_handler.setFormatter(formatter)
logger.addHandler(log_handler)
logger.setLevel(logging.INFO)


class Ex(BaseStrategy):
    def check_market_book(self, market_book):
        return True

    def process_market_book(self, market_book):
        print(market_book, market_book.total_matched)


client = clients.BacktestClient()

framework = FlumineBacktest(client=client)

strategy = Ex(market_filter={"markets": ["/tmp/marketdata/1.170212754"]})
framework.add_strategy(strategy)

strategy = Ex(market_filter={"markets": ["/tmp/marketdata/1.170223719"]})
framework.add_strategy(strategy)

strategy = Ex(
    market_filter={
        "markets": ["/tmp/marketdata/1.170223719", "/tmp/marketdata/1.170212754"]
    }
)
framework.add_strategy(strategy)

framework.run()
