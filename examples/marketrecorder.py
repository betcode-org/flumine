import time
import logging
import betfairlightweight
from pythonjsonlogger import jsonlogger

from flumine import Flumine, clients
from flumine.streams.datastream import DataStream
from strategies.marketrecorder import S3MarketRecorder

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

strategy = S3MarketRecorder(
    name="WIN",
    market_filter=betfairlightweight.filters.streaming_market_filter(
        event_type_ids=["7"],
        country_codes=["GB", "IE"],
        market_types=["WIN"],
        # market_ids=["1.169056942"],
        # event_ids=[29671376]
    ),
    stream_class=DataStream,
    context={
        "local_dir": "/tmp",
        "bucket": "fluminetest",
        "force_update": False,
        "remove_file": True,
    },
)

framework.add_strategy(strategy)

framework.run()
