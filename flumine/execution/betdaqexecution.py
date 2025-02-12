import logging
import requests
from typing import Callable
from betfairlightweight import BetfairError
from ..clients import ExchangeType
from .baseexecution import BaseExecution
from ..order.orderpackage import BaseOrderPackage

logger = logging.getLogger(__name__)


class BetdaqExecution(BaseExecution):
    EXCHANGE = ExchangeType.BETDAQ

    def execute_place(
        self, order_package: BaseOrderPackage, http_session: requests.Session
    ) -> None:
        print(123, order_package)

    def execute_cancel(
        self, order_package: BaseOrderPackage, http_session: requests.Session
    ) -> None:
        print(456, order_package)
