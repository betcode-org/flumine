import time
import logging
import betfairlightweight
from betfairlightweight.filters import streaming_market_filter
from pythonjsonlogger import jsonlogger

from flumine import Flumine, clients
from flumine.streams.datastream import DataStream
from strategies.marketrecorder import MarketRecorder

logger = logging.getLogger()

custom_format = "%(asctime) %(levelname) %(message)"
log_handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(custom_format)
formatter.converter = time.gmtime
log_handler.setFormatter(formatter)
logger.addHandler(log_handler)
logger.setLevel(logging.INFO)

trading = betfairlightweight.APIClient("username")
client = clients.BetfairClient(trading)

framework = Flumine(client=client)

# create stream(s) (market data)
stream = DataStream(
    framework,
    market_filter=streaming_market_filter(
        event_type_ids=["7"],
        country_codes=["GB", "IE"],
        market_types=["WIN"],
    ),
)
framework.add_stream(stream)

# create strategy and subscribe to stream(s)
strategy = MarketRecorder(
    name="WIN",
    streams=[stream],
    context={
        "local_dir": "/tmp",
        "force_update": False,
        "remove_file": True,
        "remove_gz_file": False,
    },
)
framework.add_strategy(strategy)

framework.run()
