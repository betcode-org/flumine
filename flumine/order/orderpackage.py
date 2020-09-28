import uuid
import time
from enum import Enum
from typing import Iterator, Optional
from betfairlightweight.metadata import order_limits

from ..events.events import BaseEvent, EventType, QueueType
from ..clients.clients import ExchangeType
from .. import config
from .order import BaseOrder, OrderStatus


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

    EVENT_TYPE = EventType.ORDER_PACKAGE
    QUEUE_TYPE = QueueType.HANDLER
    EXCHANGE = None

    def __init__(
        self,
        client,
        market_id: str,
        orders: list,
        package_type: OrderPackageType,
        bet_delay: int,
        async_: bool = False,
    ):
        super(BaseOrderPackage, self).__init__(None)
        self.id = uuid.uuid1()
        self.client = client
        self.market_id = market_id
        self._orders = orders
        self.package_type = package_type
        self.bet_delay = bet_delay  # used for simulated execution
        self.async_ = async_
        self.customer_strategy_ref = config.hostname
        self.processed = False  # used for simulated execution
        self._retry = True
        self._max_retries = 3  # will retry 3 times
        self._retry_count = 0

    def retry(self):
        if self._retry and self._retry_count < self._max_retries:
            time.sleep(self._retry_count)  # back-off
            self._retry_count += 1
            return True
        return False

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
        return [o for o in self._orders if o.status != OrderStatus.VIOLATION]

    @property
    def info(self) -> dict:
        return {
            "id": self.id,
            "client": self.client,
            "market_id": self.market_id,
            "orders": [o.id for o in self._orders],
            "package_type": self.package_type.value,
            "customer_strategy_ref": self.customer_strategy_ref,
            "bet_delay": self.bet_delay,
            "market_version": self.market_version,
            "retry": self._retry,
            "retry_count": self._retry_count,
        }

    @property
    def market_version(self) -> Optional[dict]:
        return None
        # todo return {"version": self.market.market_book.version}

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
        ]  # todo? if order.size_remaining > 0

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
