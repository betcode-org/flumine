import uuid
from enum import Enum
from typing import Iterator
from betfairlightweight.metadata import order_limits

from ..event.event import BaseEvent, EventType, QueueType
from ..clients.clients import ExchangeType
from .. import config
from .order import BaseOrder


class OrderPackageType(Enum):
    PLACE = "Place"
    CANCEL = "Cancel"
    REPLACE = "Replace"
    UPDATE = "Update"


class BaseOrderPackage(BaseEvent):

    """
    Data structure for multiple orders,
    temporary to allow execution
    """

    # todo client/retry/._orders->orders (violation)

    EVENT_TYPE = EventType.ORDER_PACKAGE
    QUEUE_TYPE = QueueType.HANDLER
    EXCHANGE = None

    def __init__(
        self,
        client,
        market_id: str,
        orders: list,
        package_type: OrderPackageType,
        market_version: dict = None,
        async_: bool = False,
    ):
        super(BaseOrderPackage, self).__init__(None)
        self.id = uuid.uuid1()
        self.client = client
        self.market_id = market_id
        self._orders = orders
        self.package_type = package_type
        self.market_version = market_version
        self.async_ = async_
        self.customer_strategy_ref = config.hostname

    @property
    def place_instructions(self) -> dict:
        raise NotImplementedError

    @property
    def cancel_instructions(self) -> dict:
        raise NotImplementedError

    @property
    def update_instructions(self) -> dict:
        raise NotImplementedError

    @property
    def replace_instructions(self) -> dict:
        raise NotImplementedError

    @classmethod
    def order_limit(cls, package_type: OrderPackageType) -> int:
        raise NotImplementedError

    @property
    def orders(self) -> list:
        return [o for o in self._orders if o]

    @property
    def info(self) -> dict:
        return {
            "id": self.id,
            "client": self.client,
            "market_id": self.market_id,
            "orders": [o.id for o in self._orders],
            "package_type": self.package_type.value,
            "customer_strategy_ref": self.customer_strategy_ref,
        }

    def __iter__(self) -> Iterator[BaseOrder]:
        return iter(self.orders)

    def __len__(self) -> int:
        return len(self.orders)


class BetfairOrderPackage(BaseOrderPackage):

    EXCHANGE = ExchangeType.BETFAIR

    @property
    def place_instructions(self):
        return [order.create_place_instruction() for order in self]

    @property
    def cancel_instructions(self):
        return [
            order.create_cancel_instruction() for order in self
        ]  # if order.size_remaining > 0

    @property
    def update_instructions(self):
        return [order.create_update_instruction() for order in self]

    @property
    def replace_instructions(self):
        return [order.create_replace_instruction() for order in self]

    @classmethod
    def order_limit(cls, package_type: OrderPackageType) -> int:
        if package_type == OrderPackageType.PLACE:
            return order_limits["placeOrders"]
        elif package_type == OrderPackageType.CANCEL:
            return order_limits["cancelOrders"]
        elif package_type == OrderPackageType.UPDATE:
            return order_limits["updateOrders"]
        elif package_type == OrderPackageType.REPLACE:
            return order_limits["replaceOrders"]
