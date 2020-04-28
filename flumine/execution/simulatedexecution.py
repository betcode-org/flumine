import requests

from .baseexecution import BaseExecution
from ..clients.clients import ExchangeType


class SimulatedExecution(BaseExecution):

    EXCHANGE = ExchangeType.SIMULATED

    def execute_place(self, order_package, http_session: requests.Session) -> None:
        raise NotImplementedError

    def execute_cancel(self, order_package, http_session: requests.Session) -> None:
        raise NotImplementedError

    def execute_update(self, order_package, http_session: requests.Session) -> None:
        raise NotImplementedError

    def execute_replace(self, order_package, http_session: requests.Session) -> None:
        raise NotImplementedError
