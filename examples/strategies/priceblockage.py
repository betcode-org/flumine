from collections import OrderedDict, defaultdict
from flumine import BaseStrategy
from flumine.order.trade import Trade
from flumine.order.order import OrderStatus
from flumine.order.ordertype import LimitOrder
from flumine.utils import get_price, get_size


class PriceBlockage(BaseStrategy):
    """
    Example strategy for inplay racing market, store
    race start time and all top level back prices in
    the market context.
    Trigger:
        - Back top of the book
        - Price > 1.5
        - Size > 100
    Order notes:
        - Seconds since start of race
        - Back size
    """

    def check_market_book(self, market, market_book):
        if market_book.status == "OPEN" and market_book.inplay:
            # store race start time in the market context
            if "start_time" not in market.context:
                market.context["start_time"] = market_book.publish_time_epoch
            return True

    def process_market_book(self, market, market_book):
        seconds_since_start = (
            market_book.publish_time_epoch - market.context["start_time"]
        ) / 1e3
        # get price dict from market context
        if "price" not in market.context:
            market.context["price"] = defaultdict(list)
        price_dict = market.context["price"]
        for runner in market_book.runners:
            # store latest prices/sizes
            back_price = get_price(runner.ex.available_to_back, 0)
            back_size = get_size(runner.ex.available_to_back, 0)
            if back_price:
                price_dict[runner.selection_id].append(
                    (market_book.publish_time_epoch, back_price, back_size)
                )
            # check trigger
            if trigger(price_dict[runner.selection_id]):
                runner_context = self.get_runner_context(
                    market.market_id, runner.selection_id, runner.handicap
                )
                if runner_context.live_trade_count == 0:
                    # back at current best back price
                    back = get_price(runner.ex.available_to_back, 0)
                    if back is None:
                        continue
                    # create trade
                    trade = Trade(
                        market_book.market_id,
                        runner.selection_id,
                        runner.handicap,
                        self,
                    )
                    # create order
                    order = trade.create_order(
                        side="BACK",
                        order_type=LimitOrder(back, self.context["stake"]),
                        notes=OrderedDict(
                            seconds_since_start=round(seconds_since_start, 2),
                            back_size=back_size,
                        ),
                    )
                    # place order for execution
                    market.place_order(order)

    def process_orders(self, market, orders):
        # kill order if unmatched in market for greater than 2 seconds
        for order in orders:
            if order.status == OrderStatus.EXECUTABLE:
                if order.elapsed_seconds and order.elapsed_seconds > 2:
                    market.cancel_order(order)


def trigger(prices: dict) -> bool:
    if prices:
        # get latest
        pt, price, size = prices[-1]
        # check price and size
        if price > 1.5 and size > 100:
            return True
    return False
