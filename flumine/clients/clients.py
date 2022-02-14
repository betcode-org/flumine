import logging
from enum import Enum

logger = logging.getLogger(__name__)


class ExchangeType(Enum):
    BETFAIR = "Betfair"
    SIMULATED = "Simulated"
    BETCONNECT = "BetConnect"


class Clients:
    """
    Data structure for flumine clients
    """

    def __init__(self) -> None:
        self._clients = []
        self._exchange_clients = {exchange.name: {} for exchange in ExchangeType}

    def login(self) -> None:
        for client in self._clients:
            client.login()
            logger.info("Client login", extra=client.extra)

    def keep_alive(self) -> None:
        for client in self._clients:
            client.keep_alive()
            logger.info("Client keep alive", extra=client.extra)

    def logout(self) -> None:
        for client in self._clients:
            client.logout()
            logger.info("Client logout", extra=client.extra)

    def update_account_details(self) -> None:
        for client in self._clients:
            client.update_account_details()
            logger.info("Client update account details", extra=client.extra)

    @property
    def extra(self) -> dict:
        return {
            k: {k_i: v_i.extra for k_i, v_i in v.items()}
            for k, v in self._exchange_clients.items()
        }

    def __iter__(self):
        return iter(self._clients)

    def __len__(self) -> int:
        return len(self._clients)
