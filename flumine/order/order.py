import uuid
import logging
import datetime
from enum import Enum
from betfairlightweight import filters

from ..clients.clients import ExchangeType
from .ordertype import BaseOrderType, OrderTypes
from .responses import Responses
from ..exceptions import OrderUpdateError

logger = logging.getLogger(__name__)


class OrderStatus(Enum):
    # Pending
    PENDING = "Pending"  # pending exchange processing
    CANCELLING = "Cancelling"  # waiting for response
    UPDATING = "Updating"  # waiting for response
    REPLACING = "Replacing"  # waiting for response
    # Completed
    EXECUTABLE = "Executable"  # an order that has a remaining unmatched portion
    EXECUTION_COMPLETE = "Execution complete"  # an order that does not have any remaining unmatched portion
    EXPIRED = "Expired"  # order is no longer available for execution due to its time in force constraint
    VOIDED = "Voided"
    LAPSED = "Lapsed"
    VIOLATION = "Violation"  # order never placed due to failing controls


class BaseOrder:

    EXCHANGE = None

    def __init__(self, trade, side: str, order_type: BaseOrderType, handicap: int = 0):
        self.id = str(uuid.uuid1().time)  # 18 char str used as unique customerOrderRef
        self.trade = trade
        self.side = side
        self.order_type = order_type
        self.handicap = handicap

        self.status = None
        self.status_log = []

        self.bet_id = None
        self._update = {}  # stores cancel/update/replace data
        self.responses = Responses()  # raw api responses

    # status
    def _update_status(self, status: OrderStatus) -> None:
        self.status_log.append(status)
        self.status = status
        logger.info("Order status update: %s" % self.status.value, extra=self.info)

    def placing(self) -> None:
        self._update_status(OrderStatus.PENDING)

    def executable(self) -> None:
        self._update_status(OrderStatus.EXECUTABLE)

    def execution_complete(self) -> None:
        self._update_status(OrderStatus.EXECUTION_COMPLETE)

    def cancelling(self) -> None:
        self._update_status(OrderStatus.CANCELLING)

    def updating(self) -> None:
        self._update_status(OrderStatus.UPDATING)

    def replacing(self) -> None:
        self._update_status(OrderStatus.REPLACING)

    def lapsed(self) -> None:
        self._update_status(OrderStatus.LAPSED)

    def voided(self) -> None:
        self._update_status(OrderStatus.VOIDED)

    def violation(self) -> None:
        self._update_status(OrderStatus.VIOLATION)

    # updates
    def place(self) -> None:
        raise NotImplementedError

    def cancel(self, size_reduction: float = None) -> None:
        raise NotImplementedError

    def update(self, new_persistence_type: str) -> None:
        raise NotImplementedError

    def replace(self, new_price: float) -> None:
        raise NotImplementedError

    # instructions
    def create_place_instruction(self) -> dict:
        raise NotImplementedError

    def create_cancel_instruction(self) -> dict:
        raise NotImplementedError

    def create_update_instruction(self) -> dict:
        raise NotImplementedError

    def create_replace_instruction(self) -> dict:
        raise NotImplementedError

    @property
    def elapsed_seconds(self):
        return (
            datetime.datetime.utcnow() - self.responses.date_time_placed
        ).total_seconds()

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
    def customer_order_ref(self) -> str:
        return "{0}-{1}".format(self.trade.strategy.name_hash, self.id)

    @property
    def info(self) -> dict:
        return {
            "market_id": self.market_id,
            "selection_id": self.selection_id,
            "handicap": self.handicap,
            "id": self.id,
            "customer_order_ref": self.customer_order_ref,
            "bet_id": self.bet_id,
            "trade": self.trade.info,
            "status": self.status.value if self.status else None,
            "status_log": ", ".join([s.value for s in self.status_log]),
        }


class BetfairOrder(BaseOrder):

    EXCHANGE = ExchangeType.BETFAIR

    # updates
    def place(self) -> None:
        self.placing()

    def cancel(self, size_reduction: float = None) -> None:
        if self.order_type.ORDER_TYPE == OrderTypes.LIMIT:
            # if size_reduction and self.size_remaining - size_reduction < 0:
            #     raise OrderUpdateError("Size reduction too large")
            if self.status != OrderStatus.EXECUTABLE:
                raise OrderUpdateError("Current status: %s" % self.status)
            self._update["size_reduction"] = size_reduction
            self.cancelling()
        else:
            raise OrderUpdateError(
                "Only LIMIT orders can be cancelled or partially cancelled once placed."
            )

    def update(self, new_persistence_type: str) -> None:
        if self.order_type.ORDER_TYPE == OrderTypes.LIMIT:
            if self.order_type.persistence_type == new_persistence_type:
                raise OrderUpdateError("Persistence types match")
            elif self.status != OrderStatus.EXECUTABLE:
                raise OrderUpdateError("Current status: %s" % self.status)
            self.order_type.persistence_type = new_persistence_type
            self.updating()
        else:
            raise OrderUpdateError("Only LIMIT orders can be updated.")

    def replace(self, new_price: float) -> None:
        if self.order_type.ORDER_TYPE in [OrderTypes.LIMIT, OrderTypes.LIMIT_ON_CLOSE]:
            if self.order_type.price == new_price:
                raise OrderUpdateError("Prices match")
            elif self.status != OrderStatus.EXECUTABLE:
                raise OrderUpdateError("Current status: %s" % self.status)
            self._update["new_price"] = new_price
            self.replacing()
        else:
            raise OrderUpdateError(
                "Only LIMIT or LIMIT_ON_CLOSE orders can be replaced."
            )

    # instructions
    def create_place_instruction(self) -> dict:
        if self.order_type.ORDER_TYPE == OrderTypes.LIMIT:
            return filters.place_instruction(
                customer_order_ref=self.customer_order_ref,
                selection_id=self.selection_id,
                side=self.side,
                order_type=self.order_type.ORDER_TYPE.name,
                limit_order=self.order_type.place_instruction(),
                handicap=self.handicap,
            )
        elif self.order_type.ORDER_TYPE == OrderTypes.LIMIT_ON_CLOSE:
            return filters.place_instruction(
                customer_order_ref=self.customer_order_ref,
                selection_id=self.selection_id,
                side=self.side,
                order_type=self.order_type.ORDER_TYPE.name,
                limit_on_close_order=self.order_type.place_instruction(),
                handicap=self.handicap,
            )
        elif self.order_type.ORDER_TYPE == OrderTypes.MARKET_ON_CLOSE:
            return filters.place_instruction(
                customer_order_ref=self.customer_order_ref,
                selection_id=self.selection_id,
                side=self.side,
                order_type=self.order_type.ORDER_TYPE.name,
                market_on_close_order=self.order_type.place_instruction(),
                handicap=self.handicap,
            )

    def create_cancel_instruction(self) -> dict:
        return filters.cancel_instruction(
            bet_id=self.bet_id, size_reduction=self._update.get("size_reduction")
        )

    def create_update_instruction(self) -> dict:
        return filters.update_instruction(
            bet_id=self.bet_id, new_persistence_type=self.order_type.persistence_type
        )

    def create_replace_instruction(self) -> dict:
        return filters.replace_instruction(
            bet_id=self.bet_id, new_price=self._update["new_price"]
        )
