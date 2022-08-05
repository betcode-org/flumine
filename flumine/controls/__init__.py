import logging

from ..order.orderpackage import OrderPackageType, BaseOrder
from ..exceptions import ControlError

logger = logging.getLogger(__name__)


class BaseControl:

    NAME = None

    def __init__(self, flumine, *args, **kwargs):
        self.flumine = flumine

    def __call__(self, order: BaseOrder, package_type: OrderPackageType):
        self._validate(order, package_type)

    def _validate(self, order: BaseOrder, package_type: OrderPackageType) -> None:
        raise NotImplementedError

    def _on_error(self, order: BaseOrder, error: str) -> None:
        violation_msg = "Order has violated: %s Error: %s" % (self.NAME, error)
        order.violation(violation_msg)
        if logger.isEnabledFor(logging.WARNING):
            logger.warning(
                violation_msg,
                extra={"control": self.NAME, "error": error, "order": order.info},
            )
        raise ControlError(violation_msg)
