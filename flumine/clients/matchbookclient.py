import logging
from typing import Optional
from flumine.clients.baseclient import BaseClient
from flumine.clients import VenueType

logger = logging.getLogger(__name__)


class MatchbookClient(BaseClient):
    """
    Matchbook betting client.
    """

    VENUE = VenueType.MATCHBOOK

    def login(self) -> None:
        self.betting_client.login()

    def keep_alive(self) -> None:
        # todo
        # self.betting_client.get_session()  # 401 if expired
        # self.betting_client.login()
        pass

    def logout(self) -> None:
        self.betting_client.logout()

    def update_account_details(self) -> None:
        # get details
        self.account_details = self.betting_client.get_account()
        # get funds
        self.account_funds = self.betting_client.get_balance()

    def min_bet_size(self) -> Optional[float]:
        return 0.10

    def min_bet_payout(self) -> Optional[float]:
        return None

    def min_bsp_liability(self) -> Optional[float]:
        return None

    @property
    def username(self) -> str:
        if self.betting_client:
            return self.betting_client.conn.username
        else:
            return self._username
