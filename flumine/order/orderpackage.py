import uuid
from enum import Enum
from typing import Iterator
from betfairlightweight.filters import (
    cancel_instruction,
    update_instruction,
    replace_instruction,
)

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

    EVENT_TYPE = EventType.ORDER_PACKAGE
    QUEUE_TYPE = QueueType.HANDLER
    EXCHANGE = None

    def __init__(
        self, client, market_id: str, orders: list, package_type: OrderPackageType
    ):
        super(BaseOrderPackage, self).__init__(None)
        self.id = uuid.uuid1()
        self.client = client
        self.market_id = market_id
        self.orders = orders
        self.package_type = package_type
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

    def __iter__(self) -> Iterator[BaseOrder]:
        return iter(self.orders)

    def __len__(self) -> int:
        return len(self.orders)


class BetfairOrderPackage(BaseOrderPackage):

    EXCHANGE = ExchangeType.BETFAIR

    @property
    def place_instructions(self):
        return [order.create_place_instructions() for order in self]

    @property
    def cancel_instructions(self):
        return [
            cancel_instruction(bet_id=order.bet_id, size_reduction=order.size_reduction)
            for order in self
            if order.size_remaining > 0
        ]

    @property
    def update_instructions(self):
        return [
            update_instruction(
                bet_id=order.bet_id,
                new_persistence_type=order.order_type.persistence_type,
            )
            for order in self
            if order.size_remaining > 0
        ]

    @property
    def replace_instructions(self):
        return [
            replace_instruction(bet_id=order.bet_id, new_price=order.new_price)
            for order in self
            if order.size_remaining > 0
        ]
