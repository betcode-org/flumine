from collections import OrderedDict
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
        if market_book.status == "OPEN" and market_book.inplay:
            return True

    def process_market_book(self, market, market_book):
        # get lowest price runner
        prices = [
            (r.selection_id, r.last_price_traded)
            for r in market_book.runners
            if r.status == "ACTIVE" and r.last_price_traded
        ]
        if not prices:
            return
        prices.sort(key=lambda tup: tup[1])
        selection_id = prices[0][0]

        if prices[0][1] > 3:
            return

        # calculate market underround for later analysis
        underround = _calculate_underround(market_book.runners)

        for runner in market_book.runners:
            if runner.selection_id == selection_id:
                runner_context = self.get_runner_context(
                    market.market_id, runner.selection_id, runner.handicap
                )
                if runner_context.live_trade_count == 0:
                    # lay at current best lay price
                    lay = get_price(runner.ex.available_to_lay, 0)
                    # create trade
                    trade = Trade(
                        market_book.market_id,
                        runner.selection_id,
                        runner.handicap,
                        self,
                    )
                    # create order
                    order = trade.create_order(
                        side="LAY",
                        order_type=LimitOrder(lay, self.context["stake"]),
                        notes=OrderedDict(underround=round(underround, 4)),
                    )
                    # place order for execution
                    market.place_order(order)

    def process_orders(self, market, orders):
        # kill order if unmatched in market for greater than 2 seconds
        for order in orders:
            if order.status == OrderStatus.EXECUTABLE:
                if order.elapsed_seconds and order.elapsed_seconds > 2:
                    market.cancel_order(order)


def _calculate_underround(runners: list) -> float:
    return sum(
        [
            1 / get_price(r.ex.available_to_lay, 0)
            for r in runners
            if r.ex.available_to_lay
        ]
    )
