import requests
import logging
from betfairlightweight import BetfairError

from .baseexecution import BaseExecution
from ..clients.clients import ExchangeType
from ..order.orderpackage import BaseOrderPackage, OrderPackageType
from ..exceptions import OrderExecutionError

logger = logging.getLogger(__name__)


class BetfairExecution(BaseExecution):

    EXCHANGE = ExchangeType.BETFAIR

    def execute_place(
        self, order_package: BaseOrderPackage, http_session: requests.Session
    ) -> None:
        place_response = self._execution_helper(self.place, order_package, http_session)
        if place_response:
            logger.info(
                "execute_place",
                extra={**order_package.info, **{"response": place_response._data}},
            )
            for (order, instruction_report) in zip(
                order_package, place_response.place_instruction_reports
            ):
                self._order_logger(
                    order, instruction_report, order_package.package_type
                )
                if instruction_report.status == "SUCCESS":
                    self._after_execution(order)

                elif instruction_report.status == "FAILURE":
                    logger.warning(
                        "execute_place FAILURE",
                        extra={
                            "order_id": order.id,
                            "status": instruction_report.status,
                            "error_code": instruction_report.error_code,
                        },
                    )
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
                    logger.error(
                        "execute_place TIMEOUT",
                        extra={
                            "order_id": order.id,
                            "status": instruction_report.status,
                            "error_code": instruction_report.error_code,
                        },
                    )

    def place(self, order_package, session):
        return order_package.client.betting_client.betting.place_orders(
            market_id=order_package.market_id,
            instructions=order_package.place_instructions,
            customer_ref=order_package.place_customer_ref.hex,
            market_version=order_package.market_version,
            customer_strategy_ref=order_package.customer_strategy_ref,
            async_=order_package.async_,
            session=session,
        )

    def execute_cancel(
        self, order_package: BaseOrderPackage, http_session: requests.Session
    ) -> None:
        cancel_response = self._execution_helper(
            self.cancel, order_package, http_session
        )
        if cancel_response:
            logger.info(
                "execute_cancel",
                extra={**order_package.info, **{"response": cancel_response._data}},
            )
            order_lookup = {o.bet_id: o for o in order_package}
            for instruction_report in cancel_response.cancel_instruction_reports:
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

    def cancel(self, order_package, session):
        cancel_instructions = list(order_package.cancel_instructions)  # temp copy
        if not cancel_instructions:
            logger.warning("Empty cancel_instructions", extra=order_package.info)
            raise OrderExecutionError()
        return order_package.client.betting_client.betting.cancel_orders(
            market_id=order_package.market_id,
            instructions=cancel_instructions,
            customer_ref=order_package.cancel_customer_ref.hex,
            session=session,
        )

    def execute_update(
        self, order_package: BaseOrderPackage, http_session: requests.Session
    ) -> None:
        raise NotImplementedError

    def execute_replace(
        self, order_package: BaseOrderPackage, http_session: requests.Session
    ) -> None:
        raise NotImplementedError

    def _execution_helper(
        self,
        trading_function,
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
            return response
        else:
            logger.warning("Empty package, not executing", extra=order_package.info)

    def _order_logger(self, order, instruction_report, package_type: OrderPackageType):
        if package_type == OrderPackageType.PLACE:
            order.responses.placed(instruction_report)
            order.bet_id = instruction_report.bet_id
        elif package_type == OrderPackageType.CANCEL:
            order.responses.cancelled(instruction_report)
        elif package_type == OrderPackageType.UPDATE:
            order.responses.updated(instruction_report)
        elif package_type == OrderPackageType.REPLACE:
            order.responses.replaced(instruction_report)
            order.bet_id = instruction_report.bet_id
        # self.flumine.log_control(order)  # todo log order

    def _after_execution(self, order):
        order.executable()
        # self.flumine.handler_queue.put(PlacedOrderEvent(order))  # todo
