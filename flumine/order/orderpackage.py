from enum import Enum

from ..event.event import BaseEvent, EventType, QueueType
from ..clients.clients import ExchangeType


class OrderPackageType(Enum):
    PLACE = "Place"
    CANCEL = "Cancel"
    REPLACE = "Replace"
    UPDATE = "Update"


class BaseOrderPackage(BaseEvent):

    """
    Data structure for multiple orders, temporary to allow execution
    """

    EVENT_TYPE = EventType.ORDER_PACKAGE
    QUEUE_TYPE = QueueType.HANDLER
    EXCHANGE = None

    def __init__(self, package_type: OrderPackageType):
        super(BaseOrderPackage, self).__init__(None)
        self.package_type = package_type


class BetfairOrderPackage(BaseOrderPackage):

    EXCHANGE = ExchangeType.BETFAIR
