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
                and runner.selection_id == 11982403
            ):
                trade = Trade(
                    market_id=market_book.market_id,
                    selection_id=runner.selection_id,
                    handicap=runner.handicap,
                    strategy=self,
                )
                order = trade.create_order(
                    side="LAY", order_type=LimitOrder(price=1.01, size=2.00)
                )
                self.place_order(market, order)

    def process_orders(self, market, orders):
        for order in orders:
            if order.status == OrderStatus.EXECUTABLE:
                if order.elapsed_seconds and order.elapsed_seconds > 5:
                    # print(order.bet_id, order.average_price_matched, order.size_matched)
                    if order.size_remaining == 2.00:
                        self.cancel_order(market, order, size_reduction=1.51)
                # self.update_order(market, order, "PERSIST")
                # if order.order_type.price == 1.01 and order.size_remaining == 0.49:
                #     self.replace_order(market, order, 1.02)
                # if order.order_type.price == 1.02:
                #     self.replace_order(market, order, 1.03)
                # if order.order_type.price == 1.03:
                #     self.replace_order(market, order, 1.05)
                pass


trading = betfairlightweight.APIClient("username")
client = clients.BetfairClient(trading)

framework = Flumine(client=client)

strategy = ExampleStrategy(
    market_filter=streaming_market_filter(market_ids=["1.170378175"]),
)
framework.add_strategy(strategy)

framework.run()
