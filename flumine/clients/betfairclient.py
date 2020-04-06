import logging
from betfairlightweight import BetfairError
from betfairlightweight import resources

from .baseclient import BaseClient
from .clients import ExchangeType

logger = logging.getLogger(__name__)


class BetfairClient(BaseClient):
    """
    Betfair betting client.
    """

    EXCHANGE = ExchangeType.BETFAIR

    def login(self) -> None:
        if self.interactive_login:
            self.betting_client.login_interactive()
        else:
            self.betting_client.login()

    def keep_alive(self) -> None:
        if self.betting_client.session_expired:
            self.betting_client.keep_alive()

    def logout(self) -> None:
        self.betting_client.logout()

    def update_account_details(self) -> None:
        # get details
        account_details = self._get_account_details()
        if account_details:
            self.account_details = account_details

        # get funds
        account_funds = self._get_account_funds()
        if account_funds:
            self.account_funds = account_funds

    def _get_account_details(self) -> resources.AccountDetails:
        try:
            return self.betting_client.account.get_account_details()
        except BetfairError as e:
            logger.error("get_account_details error", extra={"error": e}, exc_info=True)

    def _get_account_funds(self) -> resources.AccountFunds:
        try:
            return self.betting_client.account.get_account_funds()
        except BetfairError as e:
            logger.error("get_account_funds error", extra={"error": e}, exc_info=True)
