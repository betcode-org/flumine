import logging
from typing import Optional
from flumine.clients.baseclient import BaseClient
from flumine.clients import VenueType

logger = logging.getLogger(__name__)


class ToteClient(BaseClient):
    """
    Tote betting client.
    """

    VENUE = VenueType.TOTE

    def login(self) -> None:
        pass

    def keep_alive(self) -> None:
        pass

    def logout(self) -> None:
        pass

    def update_account_details(self) -> None:
        self.account_funds = self.betting_client.customer()

    def min_bet_size(self) -> Optional[float]:
        return 0.10

    def min_bet_payout(self) -> Optional[float]:
        return None

    def min_bsp_liability(self) -> Optional[float]:
        return None
