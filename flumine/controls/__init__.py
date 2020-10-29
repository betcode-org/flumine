import logging

from ..order.orderpackage import BaseOrderPackage
from ..order.order import BaseOrder

logger = logging.getLogger(__name__)


class BaseControl:

    NAME = None

    def __init__(self, flumine, *args, **kwargs):
        self.flumine = flumine

    def __call__(self, order_package: BaseOrderPackage):
        self._validate(order_package)

    def _validate(self, order_package: BaseOrderPackage) -> None:
        raise NotImplementedError

    def _on_error(self, order: BaseOrder, error: str) -> None:
        violation_msg = "Order has violated: {0} Error: {1}".format(self.NAME, error)
        order.violation(violation_msg)
        logger.warning(
            violation_msg,
            extra={"control": self.NAME, "error": error, "order": order.info},
        )
