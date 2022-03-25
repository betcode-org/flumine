import logging
from typing import Optional
from betconnect.exceptions import BetConnectException
from betconnect import resources

from .baseclient import BaseClient
from .clients import ExchangeType

logger = logging.getLogger(__name__)


class BetConnectClient(BaseClient):
    """
    BetConnect betting client.
    """

    EXCHANGE = ExchangeType.BETCONNECT

    def login(self) -> Optional[resources.Login]:
        try:
            return self.betting_client.account.login()
        except BetConnectException as e:
            logger.error(
                "BetConnectClient `account.login` error",
                exc_info=True,
                extra={
                    "client": self.betting_client,
                    "trading_function": "account.login",
                    "response": e,
                },
            )

    def keep_alive(self) -> Optional[resources.Login]:
        try:
            return self.betting_client.account.refresh_session_token()
        except BetConnectException as e:
            logger.error(
                "BetConnectClient `account.refresh_session_token` error",
                exc_info=True,
                extra={
                    "client": self.betting_client,
                    "trading_function": "account.refresh_session_token",
                    "response": e,
                },
            )

    def logout(self) -> None:
        try:
            return self.betting_client.account.logout()
        except BetConnectException as e:
            logger.error(
                "BetConnectClient `account.logout` error",
                exc_info=True,
                extra={
                    "client": self.betting_client,
                    "trading_function": "account.logout",
                    "response": e,
                },
            )

    def update_account_details(self) -> None:
        # get details
        account_details = self._get_account_details()
        if account_details:
            self.account_details = account_details
        # get funds
        account_funds = self._get_account_funds()
        if account_funds:
            self.account_funds = account_funds

    def _get_account_details(self) -> Optional[resources.AccountPreferences]:
        try:
            return self.betting_client.account.get_user_preferences()
        except BetConnectException as e:
            logger.error(
                "BetConnectClient `account.get_user_preferences` error",
                exc_info=True,
                extra={
                    "client": self.betting_client,
                    "trading_function": "account.get_user_preferences",
                    "response": e,
                },
            )

    def _get_account_funds(self) -> Optional[resources.Balance]:
        try:
            return self.betting_client.account.get_balance()
        except BetConnectException as e:
            logger.error(
                "BetConnectClient `account.get_balance` error",
                exc_info=True,
                extra={
                    "client": self.betting_client,
                    "trading_function": "account.get_balance",
                    "response": e,
                },
            )
