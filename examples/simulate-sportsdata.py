import time
import logging
from pythonjsonlogger import jsonlogger

from flumine import FlumineSimulation, clients
from flumine.strategy.strategy import BaseStrategy
from flumine.markets.middleware import SimulatedSportsDataMiddleware
from flumine.order.trade import Trade
from flumine.order.ordertype import LimitOrder

logger = logging.getLogger()

custom_format = "%(asctime) %(levelname) %(message)"
log_handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(custom_format)
formatter.converter = time.gmtime
log_handler.setFormatter(formatter)
logger.addHandler(log_handler)
logger.setLevel(logging.INFO)  # Set to logging.CRITICAL to speed up simulation


class ExampleStrategy(BaseStrategy):
    """
    Boiler plate strategy that places an
    order on the bowling team on each
    wicket.
    """

    def check_sports_data(self, market, sports_data) -> bool:
        # process_sports_data only executed if this returns True
        return True

    def process_sports_data(self, market, sports_data) -> None:
        # called on each update from sports-data-stream
        if not sports_data.match_stats:
            return
        current_innings = sports_data.match_stats.current_innings
        innings_stats = sports_data.match_stats.innings_stats[current_innings - 1]

        if (
            innings_stats.innings_wickets
            and innings_stats.innings_wickets != self.context["wickets"]
        ):
            # new wicket
            self.context["wickets"] = innings_stats.innings_wickets
            # create lookup
            lookup = {
                sports_data.home_team.name: sports_data.home_team.selection_id,
                sports_data.away_team.name: sports_data.away_team.selection_id,
            }
            selection_id = lookup[innings_stats.bowling_team]
            # place order
            trade = Trade(
                market.market_id,
                selection_id,
                0,
                self,
            )
            order = trade.create_order(
                side="BACK",
                order_type=LimitOrder(1.01, 2),
            )
            market.place_order(order)


client = clients.SimulatedClient()

framework = FlumineSimulation(client=client)

framework.add_market_middleware(
    SimulatedSportsDataMiddleware("cricketSubscription", "tests/resources/sportsdata")
)

markets = ["tests/resources/1.200806927"]

strategy = ExampleStrategy(
    market_filter={"markets": markets, "listener_kwargs": {"inplay": True}},
    context={"wickets": 0},
)
framework.add_strategy(strategy)

framework.run()

for market in framework.markets:
    print("Profit: {0:.2f}".format(sum([o.profit for o in market.blotter])))
    for order in market.blotter:
        print(
            order.selection_id,
            order.responses.date_time_placed,
            order.status,
            order.order_type.price,
            order.average_price_matched,
            order.size_matched,
            order.profit,
        )
