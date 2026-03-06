import logging
from enum import Enum
from typing import Optional

from ..exceptions import ClientError

logger = logging.getLogger(__name__)


class VenueType(Enum):
    BETFAIR = "Betfair"
    SIMULATED = "Simulated"
    BETCONNECT = "BetConnect"
    BETDAQ = "BETDAQ"
    SMARKETS = "Smarkets"
    MATCHBOOK = "Matchbook"
    POLYMARKET = "Polymarket"
    KALSHI = "Kalshi"


class Clients:
    """
    Data structure for flumine clients.
    First client added == default client
    """

    def __init__(self) -> None:
        self._clients = []
        self._venue_clients = {venue: {} for venue in VenueType}

    def add_client(self, client):
        if client in self._clients:
            raise ClientError("Client already present")
        if client.VENUE not in self._venue_clients:
            raise ClientError("Unknown venue type")
        venue = self._venue_clients[client.VENUE]
        if client.username in venue:
            raise ClientError(
                "Client username '{0}' already present in '{1}'".format(
                    client.username, client.VENUE
                )
            )
        self._clients.append(client)
        venue[client.username] = client
        logger.info("Client added", extra=client.info)
        return client

    def get_client(self, venue_type: VenueType, username: str):
        try:
            return self._venue_clients[venue_type][username]
        except KeyError:
            return

    def get_default(self, venue_type: Optional[VenueType] = None):
        if venue_type:
            return next(iter(self._venue_clients[venue_type].values()), None)
        else:
            return self._clients[0]

    def login(self) -> None:
        for client in self._clients:
            client.login()
            logger.info("Client login", extra=client.info)

    def keep_alive(self) -> None:
        for client in self._clients:
            client.keep_alive()
            logger.info("Client keep alive", extra=client.info)

    def logout(self) -> None:
        for client in self._clients:
            client.logout()
            logger.info("Client logout", extra=client.info)

    def update_account_details(self) -> None:
        for client in self._clients:
            client.update_account_details()
            logger.info("Client update account details", extra=client.info)

    @property
    def simulated(self) -> bool:
        # return True if simulated client present
        for client in self._clients:
            if client.VENUE == VenueType.SIMULATED or client.paper_trade:
                return True
        return False

    @property
    def info(self) -> dict:
        return {
            k.value: {k_i: v_i.info for k_i, v_i in v.items()}
            for k, v in self._venue_clients.items()
        }

    def __iter__(self):
        return iter(self._clients)

    def __len__(self) -> int:
        return len(self._clients)
