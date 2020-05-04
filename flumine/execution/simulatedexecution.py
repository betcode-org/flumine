import requests

from .baseexecution import BaseExecution
from ..clients.clients import ExchangeType


class SimulatedExecution(BaseExecution):

    EXCHANGE = ExchangeType.SIMULATED
    PLACE_LATENCY = 0.120
    CANCEL_LATENCY = 0.170
    UPDATE_LATENCY = 0.150  # todo confirm?
    REPLACE_LATENCY = 0.280

    def execute_place(self, order_package, http_session: requests.Session) -> None:
        raise NotImplementedError

    def execute_cancel(self, order_package, http_session: requests.Session) -> None:
        raise NotImplementedError

    def execute_update(self, order_package, http_session: requests.Session) -> None:
        raise NotImplementedError

    def execute_replace(self, order_package, http_session: requests.Session) -> None:
        raise NotImplementedError
