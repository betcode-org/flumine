import json
import uuid
import logging
import datetime
import string
import collections
from enum import Enum
from typing import Union, Optional
from betfairlightweight import filters
from betfairlightweight.resources.bettingresources import CurrentOrder

from ..clients.clients import ExchangeType
from .ordertype import LimitOrder, LimitOnCloseOrder, MarketOnCloseOrder, OrderTypes
from .responses import Responses
from ..exceptions import OrderUpdateError
from ..backtest.simulated import Simulated

logger = logging.getLogger(__name__)


VALID_BETFAIR_CUSTOMER_ORDER_REF_CHARACTERS = (
    {"-", ".", "_", "+", "*", ":", ";", "~"}
    .union(set(string.ascii_letters))
    .union(set(string.digits))
)


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

    def __init__(
        self,
        trade,
        side: str,
        order_type: Union[LimitOrder, LimitOnCloseOrder, MarketOnCloseOrder],
        handicap: float = 0,
        sep: str = "-",
        context: dict = None,
        notes: collections.OrderedDict = None,  # order notes (e.g. triggers/market state)
    ):
        self.id = str(uuid.uuid1().time)  # 18 char str used as unique customerOrderRef
        self.trade = trade
        self.side = side
        self.order_type = order_type
        self.handicap = handicap
        self.lookup = self.market_id, self.selection_id, self.handicap

        self.runner_status = None  # RunnerBook.status
        self.number_of_dead_heat_winners = None
        self.status = None
        self.status_log = []
        self.violation_msg = None
        self.context = context or {}  # store order specific notes/triggers
        self.notes = notes or collections.OrderedDict()
        self.market_notes = None  # back,lay,lpt

        self.bet_id = None
        self.update_data = {}  # stores cancel/update/replace data
        self.responses = Responses()  # raw api responses
        self.simulated = Simulated(self)  # used in simulated execution
        self._simulated = bool(self.simulated)  # cache in current class (2x quicker)
        self.publish_time = None  # marketBook.publish_time

        self.date_time_created = datetime.datetime.utcnow()
        self.date_time_execution_complete = None

        self.cleared_order = None

        self._sep = "-"  # DEFAULT VALUE
        self.sep = sep

    # status
    def _update_status(self, status: OrderStatus) -> None:
        self.status_log.append(status)
        self.status = status
        logger.info("Order status update: %s" % self.status.value, extra=self.info)
        if self.trade.complete and status != OrderStatus.VIOLATION:
            self.trade.complete_trade()

    def placing(self) -> None:
        self._update_status(OrderStatus.PENDING)

    def executable(self) -> None:
        self._update_status(OrderStatus.EXECUTABLE)
        self.update_data.clear()

    def execution_complete(self) -> None:
        self._update_status(OrderStatus.EXECUTION_COMPLETE)
        self.date_time_execution_complete = datetime.datetime.utcnow()
        self.update_data.clear()

    def cancelling(self) -> None:
        self._update_status(OrderStatus.CANCELLING)

    def updating(self) -> None:
        self._update_status(OrderStatus.UPDATING)

    def replacing(self) -> None:
        self._update_status(OrderStatus.REPLACING)

    def lapsed(self) -> None:
        self._update_status(OrderStatus.LAPSED)
        self.update_data.clear()

    def voided(self) -> None:
        self._update_status(OrderStatus.VOIDED)
        self.update_data.clear()

    def violation(self, violation_msg: str) -> None:
        self._update_status(OrderStatus.VIOLATION)
        self.violation_msg = violation_msg
        self.update_data.clear()

    # updates
    def place(self, publish_time: int) -> None:
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

    # currentOrder
    def update_current_order(self, current_order: CurrentOrder) -> None:
        self.responses.current_order = current_order

    @property
    def current_order(self) -> Union[CurrentOrder, Simulated]:
        if self._simulated:
            return self.simulated
        elif self.responses.current_order:
            return self.responses.current_order
        elif self.responses.place_response:
            return self.responses.place_response

    @property
    def complete(self) -> bool:
        """Returns False if order is
        live or pending in the market"""
        if self.status in [
            OrderStatus.PENDING,
            OrderStatus.CANCELLING,
            OrderStatus.UPDATING,
            OrderStatus.REPLACING,
            OrderStatus.EXECUTABLE,
        ]:
            return False
        elif self.status in [
            OrderStatus.EXECUTION_COMPLETE,
            OrderStatus.EXPIRED,
            OrderStatus.VOIDED,
            OrderStatus.LAPSED,
            OrderStatus.VIOLATION,
        ]:
            return True
        else:
            return False  # default to False

    @property
    def average_price_matched(self) -> float:
        raise NotImplementedError

    @property
    def sep(self) -> str:
        return self._sep

    @sep.setter
    def sep(self, new_sep: str) -> None:
        if self.is_valid_customer_order_ref_character(new_sep):
            self._sep = new_sep
        else:
            raise ValueError(f"Invalid sep: {new_sep}")

    @staticmethod
    def is_valid_customer_order_ref_character(c: str) -> bool:
        return True

    @property
    def size_matched(self) -> float:
        raise NotImplementedError

    @property
    def size_remaining(self):
        raise NotImplementedError

    @property
    def size_cancelled(self):
        raise NotImplementedError

    @property
    def size_lapsed(self):
        raise NotImplementedError

    @property
    def size_voided(self):
        raise NotImplementedError

    @property
    def elapsed_seconds(self) -> Optional[float]:
        if self.responses.date_time_placed:
            return (
                datetime.datetime.utcnow() - self.responses.date_time_placed
            ).total_seconds()
        else:
            return

    @property
    def elapsed_seconds_executable(self) -> Optional[float]:
        if self.date_time_execution_complete and self.responses.date_time_placed:
            return (
                self.date_time_execution_complete - self.responses.date_time_placed
            ).total_seconds()

    @property
    def market_id(self) -> str:
        return self.trade.market_id

    @property
    def selection_id(self) -> int:
        return self.trade.selection_id

    @property
    def customer_order_ref(self) -> str:
        return "{0}{1}{2}".format(self.trade.strategy.name_hash, self.sep, self.id)

    @property
    def notes_str(self) -> str:
        return ",".join(str(x) for x in self.notes.values())

    @property
    def info(self) -> dict:
        return {
            "market_id": self.market_id,
            "selection_id": self.selection_id,
            "handicap": self.handicap,
            "id": self.id,
            "customer_order_ref": self.customer_order_ref,
            "bet_id": self.bet_id,
            "date_time_created": str(self.date_time_created),
            "publish_time": str(self.publish_time) if self.publish_time else None,
            "trade": self.trade.info,
            "order_type": self.order_type.info,
            "info": {
                "side": self.side,
                "size_matched": self.size_matched,
                "size_remaining": self.size_remaining,
                "size_cancelled": self.size_cancelled,
                "size_lapsed": self.size_lapsed,
                "size_voided": self.size_voided,
                "average_price_matched": self.average_price_matched,
            },
            "responses": {
                "date_time_placed": str(self.responses.date_time_placed)
                if self.responses.date_time_placed
                else None,
                "elapsed_seconds_executable": self.elapsed_seconds_executable,
            },
            "runner_status": self.runner_status,
            "status": self.status.value if self.status else None,
            "status_log": ", ".join([s.value for s in self.status_log]),
            "violation_msg": self.violation_msg,
            "simulated": self.simulated.info,
            "notes": self.notes_str,
            "market_notes": self.market_notes,
        }

    def json(self) -> str:
        return json.dumps(self.info)

    def __repr__(self):
        return "Order {0}: {1}".format(
            self.bet_id, self.status.value if self.status else None
        )


class BetfairOrder(BaseOrder):

    EXCHANGE = ExchangeType.BETFAIR

    # updates
    def place(self, publish_time: int) -> None:
        self.publish_time = publish_time
        self.placing()

    def cancel(self, size_reduction: float = None) -> None:
        if self.bet_id is None:
            raise OrderUpdateError("Order does not currently have a betId")
        elif self.order_type.ORDER_TYPE == OrderTypes.LIMIT:
            if size_reduction and self.size_remaining - size_reduction < 0:
                raise OrderUpdateError("Size reduction too large")
            if self.status != OrderStatus.EXECUTABLE:
                raise OrderUpdateError("Current status: %s" % self.status)
            self.update_data["size_reduction"] = size_reduction
            self.cancelling()
        else:
            raise OrderUpdateError(
                "Only LIMIT orders can be cancelled or partially cancelled once placed"
            )

    def update(self, new_persistence_type: str) -> None:
        if self.bet_id is None:
            raise OrderUpdateError("Order does not currently have a betId")
        elif self.order_type.ORDER_TYPE == OrderTypes.LIMIT:
            if self.order_type.persistence_type == new_persistence_type:
                raise OrderUpdateError("Persistence types match")
            elif self.status != OrderStatus.EXECUTABLE:
                raise OrderUpdateError("Current status: %s" % self.status)
            self.order_type.persistence_type = new_persistence_type
            self.updating()
        else:
            raise OrderUpdateError("Only LIMIT orders can be updated")

    def replace(self, new_price: float) -> None:
        if self.bet_id is None:
            raise OrderUpdateError("Order does not currently have a betId")
        elif self.order_type.ORDER_TYPE in [
            OrderTypes.LIMIT,
            OrderTypes.LIMIT_ON_CLOSE,
        ]:
            if self.order_type.price == new_price:
                raise OrderUpdateError("Prices match")
            elif self.status != OrderStatus.EXECUTABLE:
                raise OrderUpdateError("Current status: %s" % self.status)
            self.update_data["new_price"] = new_price
            self.replacing()
        else:
            raise OrderUpdateError(
                "Only LIMIT or LIMIT_ON_CLOSE orders can be replaced"
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
            bet_id=self.bet_id, size_reduction=self.update_data.get("size_reduction")
        )

    def create_update_instruction(self) -> dict:
        return filters.update_instruction(
            bet_id=self.bet_id, new_persistence_type=self.order_type.persistence_type
        )

    def create_replace_instruction(self) -> dict:
        return filters.replace_instruction(
            bet_id=self.bet_id, new_price=self.update_data["new_price"]
        )

    # currentOrder
    @property
    def average_price_matched(self) -> float:
        try:
            return self.current_order.average_price_matched or 0.0
        except AttributeError:
            return 0.0

    @property
    def size_matched(self) -> float:
        try:
            return self.current_order.size_matched or 0.0
        except AttributeError:
            return 0.0

    @property
    def size_remaining(self):
        try:
            return self.current_order.size_remaining or 0.0
        except AttributeError:
            if self.order_type.ORDER_TYPE == OrderTypes.LIMIT:
                if (
                    self.size_matched > 0
                ):  # placeResponse does not include sizeRemaining
                    return round(self.order_type.size - self.size_matched, 2)
                else:
                    return self.order_type.size
            else:
                return self.order_type.liability

    @property
    def size_cancelled(self) -> float:
        try:
            return self.current_order.size_cancelled or 0.0
        except AttributeError:
            return 0.0

    @property
    def size_lapsed(self) -> float:
        try:
            return self.current_order.size_lapsed or 0.0
        except AttributeError:
            return 0.0

    @property
    def size_voided(self) -> float:
        try:
            return self.current_order.size_voided or 0.0
        except AttributeError:
            return 0.0

    @staticmethod
    def is_valid_customer_order_ref_character(c: str) -> bool:
        """
        Check if the separator is of length 1, and a valid
        character, as defined in the Betfair documentation is:

        CustomerRef can contain: upper/lower chars, digits, chars
         : - . _ + * : ; ~ only.
        """
        if len(c) != 1:
            return False
        else:
            return c in VALID_BETFAIR_CUSTOMER_ORDER_REF_CHARACTERS
