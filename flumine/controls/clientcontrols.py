import datetime
import logging
from betfairlightweight.metadata import transaction_limit

from ..order.orderpackage import OrderPackageType
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
        self._set_next_hour()
        self.transaction_count = 0
        self.transaction_limit = self.client.transaction_limit

    def _validate(self, order_package):
        self._check_hour()
        self.total += 1
        if order_package.package_type == OrderPackageType.PLACE:
            self._check_transaction_count(len(order_package))
            self.place_requests += len(order_package)
            if not self.safe:  # and order.flumine_order_type == "initial"
                for order in order_package:
                    self._on_error(order)
        elif order_package.package_type == OrderPackageType.CANCEL:
            self.cancel_requests += len(order_package)
        elif order_package.package_type == OrderPackageType.UPDATE:
            self.update_requests += len(order_package)
        elif order_package.package_type == OrderPackageType.REPLACE:
            self.replace_requests += len(order_package)

    def _check_hour(self):
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

    def _check_transaction_count(self, transaction_count):
        self.transaction_count += transaction_count
        if self.transaction_count > self.transaction_limit:
            logger.error(
                "Transaction limit reached",
                extra={
                    "transaction_count": self.transaction_count,
                    "transaction_limit": self.transaction_limit,
                    "client": self.client,
                },
            )

    def _set_next_hour(self):
        now = datetime.datetime.utcnow()
        self._next_hour = (now + datetime.timedelta(hours=1)).replace(
            minute=0, second=0, microsecond=0
        )

    @property
    def safe(self):
        self._check_hour()
        if self.transaction_count < self.transaction_limit:
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
