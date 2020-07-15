import logging
import requests
from concurrent.futures import ThreadPoolExecutor

from ..order.orderpackage import BaseOrderPackage, OrderPackageType, BaseOrder
from ..events.events import OrderEvent

logger = logging.getLogger(__name__)

MAX_WORKERS = 32
BET_ID_START = 100000000000  # simulated start betId->


class BaseExecution:

    EXCHANGE = None

    def __init__(self, flumine, max_workers=MAX_WORKERS):
        self.flumine = flumine
        self._max_workers = max_workers
        self._thread_pool = ThreadPoolExecutor(max_workers=self._max_workers)
        self._bet_id = BET_ID_START
        self._sessions = []
        self._sessions_created = 0

    def handler(self, order_package: BaseOrderPackage):
        """ Handles order_package, capable of place, cancel,
        replace and update.
        """
        http_session = self._get_http_session()
        if order_package.package_type == OrderPackageType.PLACE:
            func = self.execute_place
        elif order_package.package_type == OrderPackageType.CANCEL:
            func = self.execute_cancel
        elif order_package.package_type == OrderPackageType.UPDATE:
            func = self.execute_update
        elif order_package.package_type == OrderPackageType.REPLACE:
            func = self.execute_replace
        else:
            raise NotImplementedError()

        self._thread_pool.submit(func, order_package, http_session)

    def execute_place(
        self, order_package: BaseOrderPackage, http_session: requests.Session
    ) -> None:
        raise NotImplementedError

    def execute_cancel(
        self, order_package: BaseOrderPackage, http_session: requests.Session
    ) -> None:
        raise NotImplementedError

    def execute_update(
        self, order_package: BaseOrderPackage, http_session: requests.Session
    ) -> None:
        raise NotImplementedError

    def execute_replace(
        self, order_package: BaseOrderPackage, http_session: requests.Session
    ) -> None:
        raise NotImplementedError

    def _get_http_session(self) -> requests.Session:
        while self._sessions:
            try:
                return self._sessions.pop()
            except IndexError:
                continue
        self._sessions_created += 1
        logger.info(
            "New requests.Session created",
            extra={"sessions_created": self._sessions_created},
        )
        return requests.Session()

    def _return_http_session(
        self, http_session: requests.Session, err: bool = False
    ) -> None:
        if err or len(self._sessions) >= self._max_workers:
            http_session.close()
            del http_session
        else:
            self._sessions.append(http_session)

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
            self.flumine.log_control(OrderEvent(order))
        elif package_type == OrderPackageType.CANCEL:
            order.responses.cancelled(instruction_report)
        elif package_type == OrderPackageType.UPDATE:
            order.responses.updated(instruction_report)
        elif package_type == OrderPackageType.REPLACE:
            order.responses.placed(instruction_report)
            order.bet_id = instruction_report.bet_id
            self.flumine.log_control(OrderEvent(order))

    @property
    def handler_queue(self):
        return self.flumine.handler_queue

    def shutdown(self):
        logger.info("Shutting down Execution (%s)" % self.__class__.__name__)
        self._thread_pool.shutdown(wait=True)
