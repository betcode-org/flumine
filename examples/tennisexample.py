import time
import logging
import betfairlightweight
from betfairlightweight.filters import streaming_market_filter
from pythonjsonlogger import jsonlogger

from flumine import Flumine, clients, BaseStrategy
from flumine.worker import BackgroundWorker
from workers.inplayservice import poll_in_play_service

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
        # process marketBook object
        if "score" in market.context:
            score = market.context["score"]
            print(
                score.match_status,
                score.current_game,
                score.current_set,
                score.current_point,
                score.score.home.score,
                score.score.away.score,
            )


trading = betfairlightweight.APIClient("username")
client = clients.BetfairClient(trading)

framework = Flumine(client=client)

strategy = ExampleStrategy(
    market_filter=streaming_market_filter(market_ids=["1.172415939"]),
)
framework.add_strategy(strategy)

framework.add_worker(
    BackgroundWorker(
        framework,
        poll_in_play_service,
        func_kwargs={"event_type_id": "2"},
        interval=30,
        start_delay=4,
    )
)

framework.run()
