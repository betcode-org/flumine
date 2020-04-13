import requests

from .baseexecution import BaseExecution
from ..clients.clients import ExchangeType


class BetfairExecution(BaseExecution):

    EXCHANGE = ExchangeType.BETFAIR

    def execute_place(self, order_package, http_session: requests.Session) -> None:
        raise NotImplementedError

    def execute_cancel(self, order_package, http_session: requests.Session) -> None:
        raise NotImplementedError

    def execute_update(self, order_package, http_session: requests.Session) -> None:
        raise NotImplementedError

    def execute_replace(self, order_package, http_session: requests.Session) -> None:
        raise NotImplementedError
