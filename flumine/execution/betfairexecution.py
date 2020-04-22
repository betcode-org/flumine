import logging
import requests
from typing import Callable
from betfairlightweight import BetfairError

from .baseexecution import BaseExecution
from ..clients.clients import ExchangeType
from ..order.orderpackage import BaseOrderPackage, OrderPackageType, BaseOrder
from ..exceptions import OrderExecutionError

logger = logging.getLogger(__name__)


class BetfairExecution(BaseExecution):

    EXCHANGE = ExchangeType.BETFAIR

    def execute_place(
        self, order_package: BaseOrderPackage, http_session: requests.Session
    ) -> None:
        response = self._execution_helper(self.place, order_package, http_session)
        if response:
            for (order, instruction_report) in zip(
                order_package, response.place_instruction_reports
            ):
                self._order_logger(order, instruction_report, OrderPackageType.PLACE)
                if instruction_report.status == "SUCCESS":
                    order.executable()

                elif instruction_report.status == "FAILURE":
                    if instruction_report.error_code == "ERROR_IN_ORDER":
                        pass
                    elif instruction_report.error_code == "BET_TAKEN_OR_LAPSED":
                        pass
                    elif (
                        instruction_report.error_code
                        == "BET_LAPSED_PRICE_IMPROVEMENT_TOO_LARGE"
                    ):
                        pass

                elif instruction_report.status == "TIMEOUT":
                    pass

    def place(self, order_package: OrderPackageType, session: requests.Session):
        return order_package.client.betting_client.betting.place_orders(
            market_id=order_package.market_id,
            instructions=order_package.place_instructions,
            customer_ref=order_package.id.hex,
            market_version=order_package.market_version,
            customer_strategy_ref=order_package.customer_strategy_ref,
            async_=order_package.async_,
            session=session,
        )

    def execute_cancel(
        self, order_package: BaseOrderPackage, http_session: requests.Session
    ) -> None:
        response = self._execution_helper(self.cancel, order_package, http_session)
        if response:
            order_lookup = {o.bet_id: o for o in order_package}
            for instruction_report in response.cancel_instruction_reports:
                # get order (can't rely on order they are returned)
                order = order_lookup.pop(instruction_report.instruction.bet_id)
                self._order_logger(order, instruction_report, OrderPackageType.CANCEL)

                if instruction_report.status == "SUCCESS":
                    order.execution_complete()
                elif instruction_report.status == "FAILURE":
                    order.executable()
                elif instruction_report.status == "TIMEOUT":
                    order.executable()

            # reset any not returned so that they can be picked back up
            for order in order_lookup.values():
                order.executable()

    def cancel(self, order_package: OrderPackageType, session: requests.Session):
        # temp copy to prevent an empty list of instructions sent
        # this can occur if order is matched during the execution
        # cycle, resulting in all orders being cancelled!
        cancel_instructions = list(order_package.cancel_instructions)
        if not cancel_instructions:
            logger.warning("Empty cancel_instructions", extra=order_package.info)
            raise OrderExecutionError()
        return order_package.client.betting_client.betting.cancel_orders(
            market_id=order_package.market_id,
            instructions=cancel_instructions,
            customer_ref=order_package.id.hex,
            session=session,
        )

    def execute_update(
        self, order_package: BaseOrderPackage, http_session: requests.Session
    ) -> None:
        response = self._execution_helper(self.update, order_package, http_session)
        if response:
            for (order, instruction_report) in zip(  # todo check this is ok
                order_package, response.update_instruction_reports
            ):
                self._order_logger(order, instruction_report, OrderPackageType.UPDATE)

                if instruction_report.status == "SUCCESS":
                    order.executable()
                elif instruction_report.status == "FAILURE":
                    order.executable()
                elif instruction_report.status == "TIMEOUT":
                    order.executable()

    def update(self, order_package: OrderPackageType, session: requests.Session):
        return order_package.client.betting_client.betting.update_orders(
            market_id=order_package.market_id,
            instructions=order_package.update_instructions,
            customer_ref=order_package.id.hex,
            session=session,
        )

    def execute_replace(
        self, order_package: BaseOrderPackage, http_session: requests.Session
    ) -> None:
        response = self._execution_helper(self.replace, order_package, http_session)
        if response:
            for (order, instruction_report) in zip(
                order_package, response.replace_instruction_reports
            ):
                # process cancel response
                if instruction_report.cancel_instruction_reports.status == "SUCCESS":
                    self._order_logger(
                        order, instruction_report, OrderPackageType.REPLACE
                    )
                    order.execution_complete()
                # todo else?

                # process place response
                if instruction_report.place_instruction_reports.status == "SUCCESS":
                    self._order_logger(
                        order, instruction_report, OrderPackageType.REPLACE,
                    )
                    order.executable()  # todo new order?
                # todo else?

    def replace(self, order_package: OrderPackageType, session: requests.Session):
        return order_package.client.betting_client.betting.replace_orders(
            market_id=order_package.market_id,
            instructions=order_package.replace_instructions,
            customer_ref=order_package.id.hex,
            market_version=order_package.market_version,
            async_=order_package.async_,
            session=session,
        )

    def _execution_helper(  # todo retry!
        self,
        trading_function: Callable,
        order_package: BaseOrderPackage,
        http_session: requests.Session,
    ):
        if order_package.orders:
            try:
                response = trading_function(order_package, http_session)
            except BetfairError as e:
                logger.error(
                    "Execution error",
                    extra={
                        "trading_function": trading_function.__name__,
                        "response": e,
                        "order_package": order_package.info,
                    },
                )
                return
            logger.info(
                "execute_%s" % trading_function.__name__,
                extra={**order_package.info, **{"response": response._data}},
            )
            return response
        else:
            logger.warning("Empty package, not executing", extra=order_package.info)

    def _order_logger(
        self, order: BaseOrder, instruction_report, package_type: OrderPackageType
    ):
        logger.info(
            "Order %s: %s" % (package_type.value, instruction_report.status),
            extra={
                "bet_id": order.bet_id,
                "order_id": order.id,
                "status": instruction_report.status,
                "error_code": instruction_report.error_code,
            },
        )
        if package_type == OrderPackageType.PLACE:
            order.responses.placed(instruction_report)
            order.bet_id = instruction_report.bet_id
        elif package_type == OrderPackageType.CANCEL:
            order.responses.cancelled(instruction_report)
        elif package_type == OrderPackageType.UPDATE:
            order.responses.updated(instruction_report)
        elif package_type == OrderPackageType.REPLACE:
            order.responses.replaced(instruction_report)
            order.bet_id = instruction_report.place_instruction_reports.bet_id
        # self.flumine.log_control(order)  # todo log order
