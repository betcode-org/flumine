import logging

from ..order.order import OrderStatus

logger = logging.getLogger(__name__)

# https://www.betfair.com/aboutUs/Betfair.Charges/#charges6
IMPLIED_COMMISSION_RATE = 0.03


class Blotter:
    def __init__(self, market_id: str):
        self.market_id = market_id
        self._orders = {}  # {Order.id: Order}

    def strategy_orders(self, strategy) -> list:
        """Returns all orders related to a strategy.
        """
        return [order for order in self if order.trade.strategy == strategy]

    @property
    def live_orders(self) -> bool:
        for order in self._orders.values():
            if order.status == OrderStatus.EXECUTABLE:
                return True
        return False

    """ getters / setters """

    def has_order(self, customer_order_ref: str):
        return customer_order_ref in self._orders

    __contains__ = has_order

    def __setitem__(self, customer_order_ref: str, order) -> None:
        self._orders[customer_order_ref] = order

    def __getitem__(self, customer_order_ref: str):
        return self._orders[customer_order_ref]

    def __iter__(self):
        return iter(self._orders.values())

    def __len__(self) -> int:
        return len(self._orders)
