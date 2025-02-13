import logging
import requests
from betdaq import BetdaqError

from ..clients import ExchangeType
from .baseexecution import BaseExecution
from ..order.order import BaseOrder
from ..order.orderpackage import BaseOrderPackage, OrderPackageType
from ..events.events import OrderEvent

logger = logging.getLogger(__name__)


class BetdaqExecution(BaseExecution):
    EXCHANGE = ExchangeType.BETDAQ

    def execute_place(
        self, order_package: BaseOrderPackage, http_session: requests.Session
    ) -> None:
        try:
            response = order_package.client.betting_client.betting.place_orders(
                order_list=order_package.place_instructions
            )
        except BetdaqError as e:
            logger.error(
                "Execution error",
                extra={
                    "trading_function": "place_orders",
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
                    "trading_function": "place_orders",
                    "response": e,
                    "order_package": order_package.info,
                },
                exc_info=True,
            )
            return
        logger.info(
            "execute_%s" % "place_orders",
            extra={
                "trading_function": "place_orders",
                "response": response,
                "order_package": order_package.info,
            },
        )
        if response:
            for order, instruction_report in zip(order_package, response):
                with order.trade:
                    self._order_logger(
                        order, instruction_report, OrderPackageType.PLACE
                    )
                    if not instruction_report["return_code"]:
                        if int(order.id) != instruction_report["customer_reference"]:
                            logger.critical(
                                "Order id / ref missmatch",
                                extra={
                                    "order_id": int(order.id),
                                    "customer_reference": instruction_report[
                                        "customer_reference"
                                    ],
                                    "response": instruction_report,
                                },
                            )
                            continue
                        order.executable()  # let process.py pick it up
                    else:
                        logger.critical(
                            "Order error return code",
                            extra={
                                "order_id": int(order.id),
                                "return_code": instruction_report["return_code"],
                                "response": instruction_report,
                            },
                        )
                        order.execution_complete()

    def execute_cancel(
        self, order_package: BaseOrderPackage, http_session: requests.Session
    ) -> None:
        print(456, order_package)

    def _order_logger(
        self, order: BaseOrder, instruction_report: dict, package_type: OrderPackageType
    ):
        logger.info(
            "Order %s: %s",
            package_type.value,
            instruction_report["return_code"],
            extra={
                "bet_id": order.bet_id,
                "order_id": order.id,
                "return_code": instruction_report["return_code"],
            },
        )
        if package_type == OrderPackageType.PLACE:
            dt = False if order.async_ and not order.simulated else True
            order.responses.placed(instruction_report, dt=dt)
            if instruction_report["order_id"]:
                order.bet_id = instruction_report["order_id"]
                self.flumine.log_control(OrderEvent(order, exchange=order.EXCHANGE))
        elif package_type == OrderPackageType.CANCEL:
            order.responses.cancelled(instruction_report)
        elif package_type == OrderPackageType.UPDATE:
            order.responses.updated(instruction_report)
        elif package_type == OrderPackageType.REPLACE:
            order.responses.placed(instruction_report)
            order.bet_id = instruction_report["order_id"]
            self.flumine.log_control(OrderEvent(order, exchange=order.EXCHANGE))
