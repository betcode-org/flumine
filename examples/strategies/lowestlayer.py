from flumine import BaseStrategy
from flumine.order.trade import Trade
from flumine.order.order import OrderStatus
from flumine.order.ordertype import LimitOrder
from flumine.utils import get_price


class LowestLayer(BaseStrategy):
    """
    Example strategy for inplay racing market, lay order
    will be placed on current lowest priced runner.
    - Market is active and inplay
    - Lay price below 3.0
    - No live trades (EXECUTABLE orders in the market)
    - Order killed after 2 seconds if not matched
    """

    def check_market_book(self, market, market_book):
        if market_book.status not in ["CLOSED", "SUSPENDED"] and (not market_book.inplay):
            return True

    def process_market_book(self, market, market_book):
        for runner in market_book.runners:
            if runner.selection_id!=24902035:
                continue
            runner_context = self.get_runner_context(
                market.market_id, runner.selection_id
            )
            if runner_context.live_trade_count == 0:
                trade = Trade(
                    market_book.market_id,
                    runner.selection_id,
                    runner.handicap,
                    self,
                )
                order = trade.create_order(
                    side="LAY",
                    order_type=LimitOrder(
                        price=1.1,
                        size=100.0,
                        persistence_type="MARKET_ON_CLOSE"),
                )
                market.place_order(order)

