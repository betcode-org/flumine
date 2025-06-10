import logging
import requests
from typing import Callable
from betdaq import BetdaqError

from ..clients import ExchangeType
from .baseexecution import BaseExecution
from ..exceptions import OrderExecutionError
from ..order.order import BaseOrder
from ..order.orderpackage import BaseOrderPackage, OrderPackageType
from ..events.events import OrderEvent

logger = logging.getLogger(__name__)


class BetdaqExecution(BaseExecution):
    """
    BETDAQ execution for place, cancel and update, default
    single thread pool:

    'A Punter can not issue more than one order API (PlaceSingleOrder,
    PlaceGroupOrder or ChangeOrder) at the same time'
    """

    EXCHANGE = ExchangeType.BETDAQ

    def execute_place(
        self, order_package: BaseOrderPackage, http_session: requests.Session
    ) -> None:
        response = self._execution_helper(self.place, order_package)
        if response:
            order_lookup = {int(o.id): o for o in order_package}
            for instruction_report in response:
                # get order (can't rely on the order they are returned)
                order = order_lookup.pop(instruction_report["customer_reference"])
                with order.trade:
                    self._order_logger(
                        order, instruction_report, order_package.package_type
                    )
                    if not instruction_report["return_code"]:
                        order.executable()  # let process.py pick it up
                    else:
                        logger.error(
                            "execute_place: Order error return code",
                            extra={
                                "order_id": int(order.id),
                                "return_code": instruction_report["return_code"],
                                "response": instruction_report,
                            },
                        )
                        order.execution_complete()
            # todo missing order responses?
            # todo update transaction counts
        else:
            # reset on error so that they can be picked back up
            for order in order_package:
                with order.trade:
                    order.execution_complete()

    def place(self, order_package: BaseOrderPackage):
        return order_package.client.betting_client.betting.place_orders(
            order_list=order_package.place_instructions
        )

    def execute_cancel(
        self, order_package: BaseOrderPackage, http_session: requests.Session
    ) -> None:
        response = self._execution_helper(self.cancel, order_package)
        if response:
            order_lookup = {o.bet_id: o for o in order_package}
            for instruction_report in response:
                # get order (can't rely on the order they are returned)
                order = order_lookup.pop(instruction_report["order_id"])
                with order.trade:
                    self._order_logger(
                        order, instruction_report, order_package.package_type
                    )
                    order.execution_complete()
            # reset any not returned so that they can be picked back up
            for order in order_lookup.values():
                with order.trade:
                    order.executable()
        else:
            # reset on error so that they can be picked back up
            for order in order_package:
                with order.trade:
                    order.executable()

    def cancel(self, order_package: BaseOrderPackage):
        return order_package.client.betting_client.betting.cancel_orders(
            order_ids=order_package.cancel_instructions
        )

    def execute_update(
        self, order_package: BaseOrderPackage, http_session: requests.Session
    ) -> None:
        response = self._execution_helper(self.update, order_package)
        if response:
            order_lookup = {o.bet_id: o for o in order_package}
            for instruction_report in response:
                # get order (can't rely on the order they are returned)
                order = order_lookup.pop(instruction_report["order_id"])
                with order.trade:
                    self._order_logger(
                        order, instruction_report, order_package.package_type
                    )
                    if instruction_report.get("return_code"):
                        logger.error(
                            "execute_update: Order error return code",
                            extra={
                                "bet_id": order.bet_id,
                                "return_code": instruction_report["return_code"],
                                "response": instruction_report,
                            },
                        )
                        order.executable()
                    else:
                        # we don't update the order.status as we don't have a response yet
                        pass
        else:
            # reset on error so that they can be picked back up
            for order in order_package:
                with order.trade:
                    order.executable()

    def update(self, order_package: BaseOrderPackage):
        # temp copy to prevent an empty list of instructions sent
        # this can occur if order is matched during the execution
        order_list = list(order_package.update_instructions)
        if not order_list:
            logger.warning("Empty `order_list`", extra=order_package.info)
            raise OrderExecutionError()
        return order_package.client.betting_client.betting.update_orders(
            order_list=order_list
        )

    def _execution_helper(
        self,
        trading_function: Callable,
        order_package: BaseOrderPackage,
    ):
        try:
            response = trading_function(order_package)
        except BetdaqError as e:
            logger.error(
                "Execution error",
                extra={
                    "trading_function": trading_function.__name__,
                    "response": e,
                    "order_package": order_package.info,
                },
                exc_info=True,
            )
            return
        except Exception as e:
            logger.critical(
                "Execution unknown error",
                extra={
                    "trading_function": trading_function.__name__,
                    "response": e,
                    "order_package": order_package.info,
                },
                exc_info=True,
            )
            return
        logger.info(
            f"execute_{trading_function.__name__}",
            extra={
                "trading_function": trading_function.__name__,
                "response": response,
                "order_package": order_package.info,
            },
        )
        return response

    def _order_logger(
        self, order: BaseOrder, instruction_report: dict, package_type: OrderPackageType
    ):
        logger.info(
            "Order %s: %s",
            package_type.value,
            instruction_report.get("return_code"),
            extra={
                "bet_id": order.bet_id,
                "order_id": order.id,
                "return_code": instruction_report.get("return_code"),
            },
        )
        if package_type == OrderPackageType.PLACE:
            order_id = instruction_report.get("order_id")
            dt = True if order_id else False
            order.responses.placed(instruction_report, dt=dt)
            if order_id:
                order.bet_id = order_id
                self.flumine.log_control(OrderEvent(order, exchange=order.EXCHANGE))
        elif package_type == OrderPackageType.CANCEL:
            order.responses.cancelled(instruction_report)
        elif package_type == OrderPackageType.UPDATE:
            order.responses.updated(instruction_report)
