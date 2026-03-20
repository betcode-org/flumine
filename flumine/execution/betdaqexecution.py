import logging
import requests
from typing import Callable
from betdaq import BetdaqError
from concurrent.futures import ThreadPoolExecutor

from .. import config
from ..clients import VenueType
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

    Therefore this class holds two thread pools, one for
    place/update (single) and one for cancel (multi).
    """

    VENUE = VenueType.BETDAQ

    def __init__(self, flumine, max_workers: int = config.max_execution_workers):
        super().__init__(flumine, max_workers=max_workers)
        # Single thread pool for place/update
        self._thread_pool_single = ThreadPoolExecutor(max_workers=1)
        # Multi worker thread pool for cancel
        self._thread_pool_multi = ThreadPoolExecutor(max_workers=self._max_workers)

    def handler(self, order_package: BaseOrderPackage):
        """Handles order_package, capable of place, cancel,
        replace and update.
        """
        http_session = self._get_http_session()
        if order_package.package_type == OrderPackageType.PLACE:
            func = self.execute_place
            thread_pool = self._thread_pool_multi
        elif order_package.package_type == OrderPackageType.CANCEL:
            func = self.execute_cancel
            thread_pool = self._thread_pool_single
        elif order_package.package_type == OrderPackageType.UPDATE:
            func = self.execute_update
            thread_pool = self._thread_pool_multi
        elif order_package.package_type == OrderPackageType.REPLACE:
            raise NotImplementedError()
        else:
            raise NotImplementedError()
        thread_pool.submit(func, order_package, http_session)
        logger.info(
            "Thread pool submit",
            extra={
                "trading_function": func.__name__,
                "session": http_session,
                "latency": round(order_package.elapsed_seconds, 4),
                "order_package": order_package.info,
                "thread_pool": {
                    "d": thread_pool,
                    "num_threads": len(thread_pool._threads),
                    "work_queue_size": thread_pool._work_queue.qsize(),
                },
            },
        )

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
                    status = instruction_report["status"]
                    if instruction_report["return_code"]:
                        logger.error(
                            "execute_place: Order error return code",
                            extra={
                                "order_id": int(order.id),
                                "return_code": instruction_report["return_code"],
                                "response": instruction_report,
                            },
                        )
                        order.execution_complete()
                    elif status is None:
                        pass  # NoReceipt/async request pending processing
                    else:
                        order.executable()  # let process.py pick it up
            # todo update transaction counts
        else:
            # reset on error so that they can be picked back up
            for order in order_package:
                with order.trade:
                    order.execution_complete()

    def place(self, order_package: BaseOrderPackage):
        receipt = False if order_package.async_ else True
        return order_package.client.betting_client.betting.place_orders(
            order_list=order_package.place_instructions, receipt=receipt
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
            status = instruction_report.get("status")
            dt = True if status else False
            order.responses.placed(instruction_report, dt=dt)
            if order_id:
                order.bet_id = order_id
                self.flumine.log_control(OrderEvent(order, venue=order.VENUE))
        elif package_type == OrderPackageType.CANCEL:
            order.responses.cancelled(instruction_report)
        elif package_type == OrderPackageType.UPDATE:
            order.responses.updated(instruction_report)
