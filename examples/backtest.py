import time
import logging
from pythonjsonlogger import jsonlogger

from flumine import FlumineBacktest, clients
from strategies.lowestlayer import LowestLayer

logger = logging.getLogger()

custom_format = "%(asctime) %(levelname) %(message)"
log_handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
formatter.converter = time.gmtime
log_handler.setFormatter(formatter)
logger.addHandler(log_handler)
logger.setLevel(logging.INFO)

client = clients.BacktestClient()

framework = FlumineBacktest(client=client)

markets = ["tests/resources/PRO-1.170258213"]

strategy = LowestLayer(
    market_filter={"markets": markets},
    max_order_exposure=1000,
    max_selection_exposure=105,
    context={"stake": 2},
)
framework.add_strategy(strategy)

framework.run()

for market in framework.markets:
    print("Profit: {0:.2f}".format(sum([o.simulated.profit for o in market.blotter])))
    for order in market.blotter:
        print(
            order.selection_id,
            order.responses.date_time_placed,
            order.status,
            order.order_type.price,
            order.average_price_matched,
            order.size_matched,
            order.simulated.profit,
        )
