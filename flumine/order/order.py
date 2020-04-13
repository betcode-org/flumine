from enum import Enum

from ..clients.clients import ExchangeType


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

    def __init__(self, status: OrderStatus = OrderStatus.INITIAL):
        self.status = status


class BetfairOrder(BaseOrder):

    EXCHANGE = ExchangeType.BETFAIR
