import uuid
import logging
import datetime
import collections
from enum import Enum
from typing import Union, Type
from betfairlightweight.resources.bettingresources import CurrentOrder

from ..strategy.strategy import BaseStrategy
from .order import BetfairOrder
from .ordertype import LimitOrder, LimitOnCloseOrder, MarketOnCloseOrder
from ..exceptions import OrderError
from ..utils import get_market_notes

logger = logging.getLogger(__name__)


class TradeStatus(Enum):
    PENDING = "Pending"  # pending exchange processing
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
    ):
        self.id = uuid.uuid1()
        self.market_id = market_id
        self.selection_id = selection_id
        self.handicap = handicap
        self.strategy = strategy
        self.notes = (
            notes if notes else collections.OrderedDict()
        )  # trade notes (e.g. triggers/market state)
        self.market_notes = None  # back,lay,lpt
        self.fill_kill = fill_kill  # todo
        self.offset = offset  # todo
        self.green = green  # todo
        self.orders = []  # all orders linked to trade
        self.offset_orders = []  # pending offset orders once initial order has matched
        self.status_log = []
        self.status = TradeStatus.LIVE
        self.date_time_created = datetime.datetime.utcnow()
        self.date_time_complete = None

    def update_market_notes(self, market) -> None:
        self.market_notes = get_market_notes(market, self.selection_id)

    # status
    def _update_status(self, status: TradeStatus) -> None:
        self.status_log.append(status)
        self.status = status
        logger.info("Trade status update: %s" % self.status.value, extra=self.info)

    def complete_trade(self) -> None:
        self._update_status(TradeStatus.COMPLETE)
        self.date_time_complete = datetime.datetime.utcnow()
        # reset strategy context
        runner_context = self.strategy.get_runner_context(
            self.market_id, self.selection_id, self.handicap
        )
        runner_context.reset()  # todo race condition?

    @property
    def complete(self) -> bool:
        if self.status != TradeStatus.LIVE:
            return False
        if self.offset_orders:
            return False
        for order in self.orders:
            if not order.complete:
                return False
        return True

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

    def create_order_replacement(
        self, order: BetfairOrder, new_price: float
    ) -> BetfairOrder:
        """Create new order due to replace
        execution"""
        order_type = LimitOrder(
            price=new_price,
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
    def client(self):
        # 193 todo trade.client
        return self.strategy.client

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
            "market_notes": self.market_notes,
        }

    def __enter__(self):
        # todo raise error if already pending?
        self._update_status(TradeStatus.PENDING)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_tb is None:
            self._update_status(TradeStatus.LIVE)
        else:
            logger.critical("Trade error in %s" % self.id, exc_info=True)
