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
    - Order killed after 2 seconds if not matched
    """

    def check_market_book(self, live_market, market_book):
        if market_book.status not in ["CLOSED", "SUSPENDED"] and market_book.inplay:
            return True

    def process_market_book(self, live_market, market_book):
        # get lowest price runner
        prices = [
            (r.selection_id, r.last_price_traded)
            for r in market_book.runners
            if r.status == "ACTIVE"
        ]
        prices.sort(key=lambda tup: tup[1])
        selection_id = prices[0][0]

        if prices[0][1] > 3:
            return

        for runner in market_book.runners:
            if runner.selection_id == selection_id:
                # lay at current best lay price
                lay = get_price(runner.ex.available_to_lay, 0)
                trade = Trade(
                    market_book.market_id, runner.selection_id, runner.handicap, self,
                )
                order = trade.create_order(
                    side="LAY", order_type=LimitOrder(lay, self.context["stake"]),
                )
                self.place_order(live_market, order)

    def process_orders(self, market, orders):
        # kill order if unmatched in market for greater than 2 seconds
        # this logic is likely to be moved into trade.fill_kill in the future
        for order in orders:
            if order.status == OrderStatus.EXECUTABLE:
                if order.elapsed_seconds and order.elapsed_seconds > 2:
                    self.cancel_order(market, order)
