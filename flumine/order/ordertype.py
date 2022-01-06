from enum import Enum
from betfairlightweight.filters import (
    limit_order,
    limit_on_close_order,
    market_on_close_order,
)

from ..clients.clients import ExchangeType


class OrderTypes(Enum):
    LIMIT = "Limit"
    LIMIT_ON_CLOSE = "Limit on close"
    MARKET_ON_CLOSE = "Market on close"


class BaseOrderType:

    EXCHANGE = None
    ORDER_TYPE = None

    def place_instruction(self) -> dict:
        raise NotImplementedError

    @property
    def info(self):
        raise NotImplementedError


class LimitOrder(BaseOrderType):

    EXCHANGE = ExchangeType.BETFAIR
    ORDER_TYPE = OrderTypes.LIMIT

    def __init__(
        self,
        price: float,
        size: float = None,
        persistence_type: str = "LAPSE",
        time_in_force: str = None,
        min_fill_size: float = None,
        bet_target_type: str = None,
        bet_target_size: float = None,
    ):
        self.price = price
        self.size = size
        self.persistence_type = persistence_type
        self.time_in_force = time_in_force
        self.min_fill_size = min_fill_size
        self.bet_target_type = bet_target_type
        self.bet_target_size = bet_target_size

    def place_instruction(self) -> dict:
        return limit_order(
            size=self.size,
            price=self.price,
            persistence_type=self.persistence_type,
            time_in_force=self.time_in_force,
            min_fill_size=self.min_fill_size,
            bet_target_type=self.bet_target_type,
            bet_target_size=self.bet_target_size,
        )

    @property
    def info(self):
        return {
            "order_type": self.ORDER_TYPE.value,
            "price": self.price,
            "size": self.size,
            "persistence_type": self.persistence_type,
            "time_in_force": self.time_in_force,
            "min_fill_size": self.min_fill_size,
            "bet_target_type": self.bet_target_type,
            "bet_target_size": self.bet_target_size,
        }


class LimitOnCloseOrder(BaseOrderType):

    EXCHANGE = ExchangeType.BETFAIR
    ORDER_TYPE = OrderTypes.LIMIT_ON_CLOSE

    def __init__(self, liability: float, price: float):
        self.liability = liability
        self.price = price

    def place_instruction(self) -> dict:
        return limit_on_close_order(liability=self.liability, price=self.price)

    @property
    def info(self):
        return {
            "order_type": self.ORDER_TYPE.value,
            "liability": self.liability,
            "price": self.price,
        }


class MarketOnCloseOrder(BaseOrderType):

    EXCHANGE = ExchangeType.BETFAIR
    ORDER_TYPE = OrderTypes.MARKET_ON_CLOSE

    def __init__(self, liability: float):
        self.liability = liability

    def place_instruction(self) -> dict:
        return market_on_close_order(liability=self.liability)

    @property
    def info(self):
        return {
            "order_type": self.ORDER_TYPE.value,
            "liability": self.liability,
        }
