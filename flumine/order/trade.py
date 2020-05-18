import uuid
import logging
import collections
from enum import Enum
from typing import Union, Type
from betfairlightweight.resources.bettingresources import CurrentOrder

from ..strategy.strategy import BaseStrategy
from .order import BetfairOrder
from .ordertype import LimitOrder, LimitOnCloseOrder, MarketOnCloseOrder
from ..exceptions import OrderError

logger = logging.getLogger(__name__)


class TradeStatus(Enum):
    LIVE = "Live"
    COMPLETE = "Complete"


class Trade:
    def __init__(
        self,
        market_id: str,
        selection_id: int,
        handicap: float,
        strategy: BaseStrategy,
        notes: collections.OrderedDict = None,
        fill_kill=None,
        offset=None,
        green=None,
        stop=None,
    ):
        self.id = uuid.uuid1()
        self.market_id = market_id
        self.selection_id = selection_id
        self.handicap = handicap
        self.strategy = strategy
        self.notes = (
            notes if notes else collections.OrderedDict()
        )  # trade notes (e.g. triggers/market state)
        self.fill_kill = fill_kill
        self.offset = offset
        self.green = green
        self.stop = stop
        self.orders = []  # all orders linked to trade
        self.offset_orders = []  # pending offset orders once initial order has matched
        self.status_log = []
        self.status = TradeStatus.LIVE

    # status
    def _update_status(self, status: TradeStatus) -> None:
        self.status_log.append(status)
        self.status = status
        logger.info("Trade status update: %s" % self.status.value, extra=self.info)

    def complete(self) -> None:
        self._update_status(TradeStatus.COMPLETE)
        # reset strategy context
        runner_context = self.strategy.get_runner_context(
            self.market_id, self.selection_id, self.handicap
        )
        runner_context.reset()  # todo race condition?

    def create_order(
        self,
        side: str,
        order_type: Union[LimitOrder, LimitOnCloseOrder, MarketOnCloseOrder],
        handicap: float = 0,
        order: Type[BetfairOrder] = BetfairOrder,
    ) -> BetfairOrder:
        if order_type.EXCHANGE != order.EXCHANGE:
            raise OrderError(
                "Incorrect order/order_type exchange combination for trade.create_order"
            )
        order = order(trade=self, side=side, order_type=order_type, handicap=handicap)
        self.orders.append(order)
        return order

    def create_order_replacement(self, order: BetfairOrder) -> BetfairOrder:
        """Create new order due to replace
        execution"""
        order_type = LimitOrder(
            price=order.update_data["new_price"],
            size=order.order_type.size,
            persistence_type=order.order_type.persistence_type,
        )
        order = BetfairOrder(
            trade=self, side=order.side, order_type=order_type, handicap=order.handicap
        )
        self.orders.append(order)
        return order

    def create_order_from_current(
        self, current_order: CurrentOrder, order_id: str
    ) -> BetfairOrder:
        if current_order.order_type == "LIMIT":
            order_type = LimitOrder(
                current_order.price_size.price,
                current_order.price_size.size,
                current_order.persistence_type,
            )
        else:
            raise NotImplementedError
        order = BetfairOrder(
            trade=self,
            side=current_order.side,
            order_type=order_type,
            handicap=current_order.handicap,
        )
        order.bet_id = current_order.bet_id
        order.id = order_id
        self.orders.append(order)
        return order

    @property
    def notes_str(self) -> str:
        return ",".join(str(x) for x in self.notes.values())

    @property
    def info(self) -> dict:
        return {
            "id": self.id,
            "strategy": self.strategy,
            "status": self.status,
            "orders": [o.id for o in self.orders],
            "notes": self.notes_str,
        }
