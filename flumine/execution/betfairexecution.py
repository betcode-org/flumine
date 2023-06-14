import logging
import requests
from typing import Callable
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
        response = self._execution_helper(self.place, order_package, http_session)
        if response:
            for order, instruction_report in zip(
                order_package, response.place_instruction_reports
            ):
                with order.trade:
                    self._order_logger(
                        order, instruction_report, OrderPackageType.PLACE
                    )
                    if instruction_report.status == "SUCCESS":
                        if instruction_report.order_status == "PENDING":
                            pass  # async request pending processing
                        else:
                            order.executable()  # let process.py pick it up
                    elif instruction_report.status == "FAILURE":
                        order.execution_complete()
                    elif instruction_report.status == "TIMEOUT":
                        # https://docs.developer.betfair.com/display/1smk3cen4v3lu3yomq5qye0ni/Betting+Enums#BettingEnums-ExecutionReportStatus
                        pass

            # update transaction counts
            order_package.client.add_transaction(len(order_package))

    def place(self, order_package: BaseOrderPackage, session: requests.Session):
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
            failed_transaction_count = 0
            order_lookup = {o.bet_id: o for o in order_package}
            for instruction_report in response.cancel_instruction_reports:
                # get order (can't rely on the order they are returned)
                order = order_lookup.pop(instruction_report.instruction.bet_id)
                with order.trade:
                    self._order_logger(
                        order, instruction_report, OrderPackageType.CANCEL
                    )
                    if instruction_report.status == "SUCCESS":
                        if (
                            instruction_report.size_cancelled == order.size_remaining
                            or order.size_remaining
                            == 0  # handle orders stream update / race condition
                        ):
                            order.execution_complete()
                        else:
                            order.executable()
                    elif instruction_report.status == "FAILURE":
                        if instruction_report.error_code == "BET_TAKEN_OR_LAPSED":
                            order.execution_complete()
                        else:
                            order.executable()
                        failed_transaction_count += 1
                    elif instruction_report.status == "TIMEOUT":
                        order.executable()

            # reset any not returned so that they can be picked back up
            for order in order_lookup.values():
                with order.trade:
                    order.executable()

            # update transaction counts
            if failed_transaction_count:
                order_package.client.add_transaction(
                    failed_transaction_count, failed=True
                )

    def cancel(self, order_package: BaseOrderPackage, session: requests.Session):
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
            failed_transaction_count = 0
            for order, instruction_report in zip(
                order_package, response.update_instruction_reports
            ):
                with order.trade:
                    self._order_logger(
                        order, instruction_report, OrderPackageType.UPDATE
                    )
                    if instruction_report.status == "SUCCESS":
                        order.executable()
                    elif instruction_report.status == "FAILURE":
                        order.executable()
                        failed_transaction_count += 1
                    elif instruction_report.status == "TIMEOUT":
                        order.executable()

            # update transaction counts
            if failed_transaction_count:
                order_package.client.add_transaction(
                    failed_transaction_count, failed=True
                )

    def update(self, order_package: BaseOrderPackage, session: requests.Session):
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
            failed_transaction_count = 0
            market = self.flumine.markets.markets[order_package.market_id]
            for order, instruction_report in zip(
                order_package, response.replace_instruction_reports
            ):
                with order.trade:
                    # process cancel response
                    if (
                        instruction_report.cancel_instruction_reports.status
                        == "SUCCESS"
                    ):
                        self._order_logger(
                            order,
                            instruction_report.cancel_instruction_reports,
                            OrderPackageType.CANCEL,
                        )
                        order.execution_complete()
                    elif (
                        instruction_report.cancel_instruction_reports.status
                        == "FAILURE"
                    ):
                        order.executable()
                        failed_transaction_count += 1
                    elif (
                        instruction_report.cancel_instruction_reports.status
                        == "TIMEOUT"
                    ):
                        order.executable()

                    # process place response
                    if instruction_report.place_instruction_reports.status == "SUCCESS":
                        # create new order
                        replacement_order = order.trade.create_order_replacement(
                            order,
                            instruction_report.place_instruction_reports.instruction.limit_order.price,
                            instruction_report.place_instruction_reports.instruction.limit_order.size,
                            order_package.date_time_created,
                        )
                        self._order_logger(
                            replacement_order,
                            instruction_report.place_instruction_reports,
                            OrderPackageType.REPLACE,
                        )
                        # add to blotter
                        market.place_order(
                            replacement_order, execute=False, client=order.client
                        )
                        replacement_order.executable()
                    elif (
                        instruction_report.place_instruction_reports.status == "FAILURE"
                    ):
                        pass  # todo
                    elif (
                        instruction_report.place_instruction_reports.status == "TIMEOUT"
                    ):
                        pass  # todo

            # update transaction counts
            order_package.client.add_transaction(len(order_package))
            if failed_transaction_count:
                order_package.client.add_transaction(
                    failed_transaction_count, failed=True
                )

    def replace(self, order_package: BaseOrderPackage, session: requests.Session):
        return order_package.client.betting_client.betting.replace_orders(
            market_id=order_package.market_id,
            instructions=order_package.replace_instructions,
            customer_ref=order_package.id.hex,
            market_version=order_package.market_version,
            async_=order_package.async_,
            session=session,
        )

    def _execution_helper(
        self,
        trading_function: Callable,
        order_package: BaseOrderPackage,
        http_session: requests.Session,
    ):
        if order_package.elapsed_seconds > 0.1 and order_package.retry_count == 0:
            logger.warning(
                "High latency between current time and OrderPackage creation time, it is likely that the thread pool is currently exhausted",
                extra={
                    "trading_function": trading_function.__name__,
                    "session": http_session,
                    "latency": round(order_package.elapsed_seconds, 3),
                    "order_package": order_package.info,
                    "thread_pool": {
                        "num_threads": len(self._thread_pool._threads),
                        "work_queue_size": self._thread_pool._work_queue.qsize(),
                    },
                },
            )
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
                    exc_info=True,
                )
                if order_package.retry():
                    self.handler(order_package)
                else:
                    # reset orders
                    if order_package.package_type == OrderPackageType.PLACE:
                        order_package.reset_orders(complete=True)
                    else:
                        order_package.reset_orders()

                self._return_http_session(http_session, err=True)
                return
            except Exception as e:
                logger.critical(
                    "Execution unknown error",
                    extra={
                        "trading_function": trading_function.__name__,
                        "exception": e,
                        "order_package": order_package.info,
                    },
                    exc_info=True,
                )
                self._return_http_session(http_session, err=True)
                return
            logger.info(
                "execute_%s" % trading_function.__name__,
                extra={
                    "trading_function": trading_function.__name__,
                    "elapsed_time": response.elapsed_time,
                    "response": response._data,
                    "order_package": order_package.info,
                },
            )
            self._return_http_session(http_session)
            return response
        else:
            logger.warning("Empty package, not executing", extra=order_package.info)
            self._return_http_session(http_session)
