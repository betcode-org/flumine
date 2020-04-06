import time
import logging
import betfairlightweight
from pythonjsonlogger import jsonlogger

from flumine import FlumineBacktest, BaseStrategy
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


trading = betfairlightweight.APIClient("username")

framework = FlumineBacktest(trading=trading, interactive=True)

strategy = Ex(
    market_filter={"markets": ["/tmp/marketdata/1.167775532"]},
    stream_class=HistoricalStream,
)

framework.add_strategy(strategy)

framework.run()
