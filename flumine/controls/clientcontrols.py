import datetime
import logging
from typing import Optional
from betfairlightweight.metadata import transaction_limit

from ..order.orderpackage import BaseOrder, OrderPackageType
from . import BaseControl
from ..clients.baseclient import BaseClient

logger = logging.getLogger(__name__)


class MaxOrderCount(BaseControl):

    """
    Counts and limits orders based on max
    order count.
    Only prevents placeOrders if limit is
    reached.
    """

    NAME = "MAX_ORDER_COUNT"

    def __init__(self, flumine, client: BaseClient):
        super(MaxOrderCount, self).__init__(flumine)
        self.client = client
        self.total = 0
        self.place_requests = 0
        self.cancel_requests = 0
        self.update_requests = 0
        self.replace_requests = 0
        self._next_hour = None
        self.transaction_count = 0

    def _validate(self, order: BaseOrder, package_type: OrderPackageType) -> None:
        if self._next_hour is None:
            self._set_next_hour()
        self._check_hour()
        self.total += 1
        if package_type == OrderPackageType.PLACE:
            self._check_transaction_count(1)
            self.place_requests += 1
            if not self.safe:
                self._on_error(
                    order,
                    "Max Order Count has been reached ({0}) for current hour".format(
                        self.transaction_count
                    ),
                )
        elif package_type == OrderPackageType.CANCEL:
            self.cancel_requests += 1
        elif package_type == OrderPackageType.UPDATE:
            self.update_requests += 1
        elif package_type == OrderPackageType.REPLACE:
            self.replace_requests += 1

    def _check_hour(self) -> None:
        if datetime.datetime.utcnow() > self._next_hour:
            logger.info(
                "Execution new hour",
                extra={
                    "transaction_count": self.transaction_count,
                    "place_requests": self.place_requests,
                    "cancel_requests": self.cancel_requests,
                    "update_requests": self.update_requests,
                    "replace_requests": self.replace_requests,
                    "client": self.client,
                },
            )
            self._set_next_hour()
            if self.transaction_count > transaction_limit:
                self.client.chargeable_transaction_count += (
                    self.transaction_count - transaction_limit
                )
            self.transaction_count = 0

    def _check_transaction_count(self, transaction_count: int) -> None:
        self.transaction_count += transaction_count
        if self.transaction_limit and self.transaction_count > self.transaction_limit:
            logger.error(
                "Transaction limit reached",
                extra={
                    "transaction_count": self.transaction_count,
                    "transaction_limit": self.transaction_limit,
                    "client": self.client,
                },
            )

    def _set_next_hour(self) -> None:
        now = datetime.datetime.utcnow()
        self._next_hour = (now + datetime.timedelta(hours=1)).replace(
            minute=0, second=0, microsecond=0
        )

    @property
    def safe(self) -> bool:
        self._check_hour()
        if self.transaction_limit is None:
            return True
        elif self.transaction_count < self.transaction_limit:
            return True
        else:
            logger.error(
                "Transaction limit reached",
                extra={
                    "transaction_count": self.transaction_count,
                    "transaction_limit": self.transaction_limit,
                    "client": self.client,
                },
            )
            return False

    @property
    def transaction_limit(self) -> Optional[int]:
        return self.client.transaction_limit
