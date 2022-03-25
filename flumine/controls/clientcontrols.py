import datetime
import logging
import threading
from typing import Optional

from ..order.orderpackage import BaseOrder, OrderPackageType
from . import BaseControl
from ..clients import BaseClient

logger = logging.getLogger(__name__)


class MaxTransactionCount(BaseControl):

    """
    Counts and limits orders based on max
    transaction count as per:
        - https://www.betfair.com/aboutUs/Betfair.Charges/#TranCharges2
        - 5000 transactions per hour
        - `A ‘transaction’ shall include all bets placed and all failed transactions`
    Counts are updated after an execution,
    thread safe due to the execution pool.
    """

    NAME = "MAX_TRANSACTION_COUNT"

    def __init__(self, flumine, client: BaseClient):
        super(MaxTransactionCount, self).__init__(flumine)
        self.client = client
        self._next_hour = None
        # this hour
        self.current_transaction_count = 0
        self.current_failed_transaction_count = 0
        # total since start
        self.transaction_count = 0
        self.failed_transaction_count = 0
        # thread lock
        self._lock = threading.Lock()

    def add_transaction(self, count: int, failed: bool = False) -> None:
        with self._lock:
            if failed:
                self.failed_transaction_count += count
                self.current_failed_transaction_count += count
            else:
                self.transaction_count += count
                self.current_transaction_count += count

    def _validate(self, order: BaseOrder, package_type: OrderPackageType) -> None:
        self._check_hour()
        if not self.safe:
            self._on_error(
                order,
                "Max Transaction Count has been reached ({0}) for current hour".format(
                    self.current_transaction_count_total
                ),
            )

    def _check_hour(self) -> None:
        now = datetime.datetime.utcnow()
        next_hour = now + datetime.timedelta(hours=1)
        if self._next_hour is None:
            self._set_next_hour()
        elif (
            self._next_hour.date() != next_hour.date()
            or self._next_hour.hour != next_hour.hour
        ):
            logger.info(
                "Execution new hour",
                extra={
                    "current_transaction_count_total": self.current_transaction_count_total,
                    "current_transaction_count": self.current_transaction_count,
                    "current_failed_transaction_count": self.current_failed_transaction_count,
                    "total_transaction_count": self.transaction_count,
                    "total_failed_transaction_count": self.failed_transaction_count,
                    "client": self.client.info,
                },
            )
            self._set_next_hour()

    def _set_next_hour(self) -> None:
        now = datetime.datetime.utcnow()
        self._next_hour = (now + datetime.timedelta(hours=1)).replace(
            minute=0, second=0, microsecond=0
        )
        self.current_transaction_count = 0
        self.current_failed_transaction_count = 0

    @property
    def safe(self) -> bool:
        if self.transaction_limit is None:
            return True
        elif self.current_transaction_count_total <= self.transaction_limit:
            return True
        else:
            logger.error(
                "Transaction limit reached",
                extra={
                    "current_transaction_count_total": self.current_transaction_count_total,
                    "current_transaction_count": self.current_transaction_count,
                    "current_failed_transaction_count": self.current_failed_transaction_count,
                    "transaction_limit": self.transaction_limit,
                    "client": self.client.info,
                },
            )
            return False

    @property
    def current_transaction_count_total(self) -> int:
        return self.current_transaction_count + self.current_failed_transaction_count

    @property
    def transaction_count_total(self) -> int:
        return self.transaction_count + self.failed_transaction_count

    @property
    def transaction_limit(self) -> Optional[int]:
        return self.client.transaction_limit
