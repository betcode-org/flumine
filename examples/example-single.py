import time
import logging
import betfairlightweight
from betfairlightweight.filters import (
    streaming_market_filter,
    streaming_market_data_filter,
)
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


class SingleStrategy(BaseStrategy):
    def check_market_book(self, market, market_book):
        # process_market_book only executed if this returns True
        if market.market_catalogue is None:
            return False  # wait for catalogue
        if market_book.status == "OPEN" and not market_book.inplay:
            return True

    def process_market_book(self, market, market_book):
        # get context
        selections = self.context["selections"]
        for selection in selections:
            if market_book.market_id == selection["market_id"]:
                for runner in market_book.runners:
                    runner_context = self.get_runner_context(
                        market.market_id, runner.selection_id, runner.handicap
                    )
                    if runner_context.trade_count > 0:
                        continue
                    if (
                        runner.status == "ACTIVE"
                        and runner.selection_id == selection["selection_id"]
                    ):
                        trade = Trade(
                            market_id=market_book.market_id,
                            selection_id=runner.selection_id,
                            handicap=runner.handicap,
                            strategy=self,
                        )
                        order = trade.create_order(
                            side=selection["side"],
                            order_type=LimitOrder(
                                price=1.01, size=selection["liability"]
                            ),
                        )
                        market.place_order(order)


trading = betfairlightweight.APIClient("username")
client = clients.BetfairClient(trading)

framework = Flumine(client=client)

strategy = SingleStrategy(
    name="back_strat_42",
    market_filter=streaming_market_filter(
        event_type_ids=["7"],
        country_codes=["GB", "IE"],
        market_types=["WIN"],
    ),
    market_data_filter=streaming_market_data_filter(
        fields=[
            "EX_BEST_OFFERS",
            "EX_LTP",
            "EX_MARKET_DEF",
        ],
        ladder_levels=1,
    ),
    conflate_ms=1000,  # update every 1s
    max_trade_count=1,  # 1 trade/order per selection only
    context={
        "selections": [
            {
                "market_id": "1.196154851",
                "selection_id": 28247970,
                "side": "LAY",
                "liability": 10.0,
            }
            # add more here..
        ]
    },
)
framework.add_strategy(strategy)

framework.run()
