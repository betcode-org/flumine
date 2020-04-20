import uuid
from typing import Type

from ..strategy.strategy import BaseStrategy
from .order import BaseOrder, BetfairOrder, BaseOrderType
from ..exceptions import OrderError


class Trade:
    def __init__(
        self,
        market_id: str,
        selection_id: int,
        strategy: BaseStrategy,
        fill_kill=None,
        offset=None,
        green=None,
        stop=None,
    ):
        self.id = uuid.uuid1()
        self.market_id = market_id
        self.selection_id = selection_id
        self.strategy = strategy
        self.fill_kill = fill_kill
        self.offset = offset
        self.green = green
        self.stop = stop
        self.orders = []  # all orders linked to trade
        self.status = None  # todo? OPEN/COMPLETE

    def create_order(
        self,
        side: str,
        order_type: BaseOrderType,
        handicap: int = 0,
        order: Type[BaseOrder] = BetfairOrder,
    ):
        if order_type.EXCHANGE != order.EXCHANGE:
            raise OrderError(
                "Incorrect order/order_type exchange combination for trade.create_order"
            )
        order = order(trade=self, side=side, order_type=order_type, handicap=handicap)
        self.orders.append(order)
        return order

    @property
    def info(self) -> dict:
        return {
            "id": self.id,
            "strategy": self.strategy,
            "status": self.status,
            "orders": [o.id for o in self.orders],
        }
