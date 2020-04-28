import logging

# from ..order.process import strategy_reset
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

    def _on_error(self, order: BaseOrder) -> None:
        order.violation()
        logger.warning(
            "Order has violated {0} and will not be placed".format(self.NAME),
            extra=order.info,
        )
        # if order.flumine_order_type == "initial":
        #     strategy_reset(order)
