import uuid
from enum import Enum

from ..clients.clients import ExchangeType
from .trade import Trade
from .ordertype import BaseOrderType


class OrderStatus(Enum):
    # Pending
    INITIAL = "Initial"  # waiting for execution
    PLACING = "Placing"  # waiting for response
    CANCELLING = "Cancelling"  # waiting for response
    UPDATING = "Updating"  # waiting for response
    REPLACING = "Replacing"  # waiting for response
    # Completed
    CANCELLED = "Cancelled"
    OFFSET = "Offset"
    GREENING = "Greening"
    STOPPED = "Stopped"
    Violation = "Violation"
    VOIDED = "Voided"
    LAPSED = "Lapsed"


class BaseOrder:

    EXCHANGE = None

    def __init__(
        self,
        trade: Trade,
        side: str,
        order_type: BaseOrderType,
        handicap: int = 0,
        status: OrderStatus = OrderStatus.INITIAL,
    ):
        self.id = uuid.uuid1()
        self.trade = trade
        self.side = side
        self.order_type = order_type
        self.handicap = handicap

        self.status = status
        self.status_log = [status]

        self.bet_id = None

    @property
    def market_id(self) -> str:
        return self.trade.market_id

    @property
    def selection_id(self) -> int:
        return self.trade.selection_id

    @property
    def lookup(self) -> tuple:
        return self.market_id, self.selection_id, self.handicap

    @property
    def id_int(self) -> int:
        return self.id.time  # 18 char int used as unique customerOrderRef


class BetfairOrder(BaseOrder):

    EXCHANGE = ExchangeType.BETFAIR
