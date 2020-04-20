import time
import logging
import betfairlightweight
from betfairlightweight.filters import streaming_market_filter
from pythonjsonlogger import jsonlogger

from flumine import Flumine, clients, BaseStrategy
from flumine.order.trade import Trade
from flumine.order.ordertype import LimitOrder

logger = logging.getLogger()

custom_format = "%(asctime) %(levelname) %(message)"
log_handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(custom_format)
formatter.converter = time.gmtime
log_handler.setFormatter(formatter)
logger.addHandler(log_handler)
logger.setLevel(logging.INFO)


class ExampleStrategy(BaseStrategy):
    def start(self):
        # subscribe to streams
        print("starting strategy 'ExampleStrategy'")

    def check_market_book(self, market, market_book):
        # process_market_book only executed if this returns True
        if market_book.status != "CLOSED":
            return True

    def process_market_book(self, market, market_book):
        # process marketBook object
        for runner in market_book.runners:
            if (
                runner.status == "ACTIVE"
                and runner.last_price_traded
                and runner.last_price_traded < 3
            ):
                trade = Trade(
                    market_id=market_book.market_id,
                    selection_id=runner.selection_id,
                    strategy=self,
                )
                order = trade.create_order(
                    side="LAY", order_type=LimitOrder(price=1.01, size=2.00)
                )
                self.place_order(market, order)

    def process_orders(self, market, orders):
        for order in orders:
            print(order.status)


trading = betfairlightweight.APIClient("username")
client = clients.BetfairClient(trading)

framework = Flumine(client=client)

strategy = ExampleStrategy(
    market_filter=streaming_market_filter(market_ids=["1.170314815"]),
    streaming_timeout=2,
)
framework.add_strategy(strategy)

framework.run()
