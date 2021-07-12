import time
import logging
import requests
from concurrent.futures import ThreadPoolExecutor

from ..order.orderpackage import BaseOrderPackage, OrderPackageType, BaseOrder
from ..events.events import OrderEvent

logger = logging.getLogger(__name__)

MAX_SESSION_AGE = 200  # seconds since last request
BET_ID_START = 100000000000  # simulated start betId->


class BaseExecution:

    EXCHANGE = None

    def __init__(self, flumine, max_workers: int = None):
        self.flumine = flumine
        self._max_workers = max_workers
        self._thread_pool = ThreadPoolExecutor(max_workers=self._max_workers)
        self._bet_id = BET_ID_START
        self._sessions = []
        self._sessions_created = 0

    def handler(self, order_package: BaseOrderPackage):
        """Handles order_package, capable of place, cancel,
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
        logger.info(
            "Thread pool submit",
            extra={
                "trading_function": func.__name__,
                "session": http_session,
                "latency": round(order_package.elapsed_seconds, 4),
                "order_package": order_package.info,
                "thread_pool": {
                    "num_threads": len(self._thread_pool._threads),
                    "work_queue_size": self._thread_pool._work_queue.qsize(),
                },
            },
        )

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
                _session = self._sessions.pop(0)
                if (time.time() - _session.time_returned) > MAX_SESSION_AGE:
                    self._return_http_session(_session, err=True)
                    continue
                else:
                    return _session
            except IndexError:
                continue
        return self._create_new_session()

    def _create_new_session(self) -> requests.Session:
        session = requests.Session()
        session.time_created = time.time()
        session.time_returned = time.time()
        self._sessions_created += 1
        logger.info(
            "New requests.Session created",
            extra={
                "sessions_created": self._sessions_created,
                "session": session,
                "session_time_created": session.time_created,
                "session_time_returned": session.time_returned,
                "live_sessions_count": len(self._sessions),
            },
        )
        return session

    def _return_http_session(
        self, http_session: requests.Session, err: bool = False
    ) -> None:
        if err or len(self._sessions) >= self._max_workers:
            logger.info(
                "Deleting requests.Session",
                extra={
                    "sessions_created": self._sessions_created,
                    "session": http_session,
                    "session_time_created": http_session.time_created,
                    "session_time_returned": http_session.time_returned,
                    "live_sessions_count": len(self._sessions),
                    "err": err,
                },
            )
            del http_session
        else:
            http_session.time_returned = time.time()
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
            if instruction_report.bet_id:
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

    def shutdown(self):
        logger.info("Shutting down Execution (%s)" % self.__class__.__name__)
        self._thread_pool.shutdown(wait=True)
