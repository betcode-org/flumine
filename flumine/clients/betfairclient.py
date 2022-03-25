import logging
from typing import Optional
from betfairlightweight import BetfairError, resources
from betfairlightweight.metadata import currency_parameters

from .baseclient import BaseClient
from .clients import ExchangeType

logger = logging.getLogger(__name__)

# default to GBP on error
MIN_BET_SIZE = currency_parameters["GBP"]["min_bet_size"]
MIN_BSP_LIABILITY = currency_parameters["GBP"]["min_bsp_liability"]
MIN_BET_PAYOUT = currency_parameters["GBP"]["min_bet_payout"]


class BetfairClient(BaseClient):
    """
    Betfair betting client.
    """

    EXCHANGE = ExchangeType.BETFAIR

    def login(self) -> Optional[resources.LoginResource]:
        try:
            if self.interactive_login:
                return self.betting_client.login_interactive()
            else:
                return self.betting_client.login()
        except BetfairError as e:
            logger.error(
                "BetfairClient `login` error",
                exc_info=True,
                extra={
                    "client": self.betting_client,
                    "trading_function": "login",
                    "response": e,
                },
            )

    def keep_alive(self) -> Optional[resources.KeepAliveResource]:
        if self.betting_client.session_expired:
            try:
                return self.betting_client.keep_alive()
            except BetfairError as e:
                logger.error(
                    "BetfairClient `keep_alive` error",
                    exc_info=True,
                    extra={
                        "client": self.betting_client,
                        "trading_function": "keep_alive",
                        "response": e,
                    },
                )

    def logout(self) -> Optional[resources.LogoutResource]:
        try:
            return self.betting_client.logout()
        except BetfairError as e:
            logger.error(
                "BetfairClient `logout` error",
                exc_info=True,
                extra={
                    "client": self.betting_client,
                    "trading_function": "logout",
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

    def _get_account_details(self) -> Optional[resources.AccountDetails]:
        try:
            return self.betting_client.account.get_account_details()
        except BetfairError as e:
            logger.error(
                "BetfairClient `account.get_account_details` error",
                exc_info=True,
                extra={
                    "client": self.betting_client,
                    "trading_function": "account.get_account_details",
                    "response": e,
                },
            )

    def _get_account_funds(self) -> Optional[resources.AccountFunds]:
        try:
            return self.betting_client.account.get_account_funds()
        except BetfairError as e:
            logger.error(
                "BetfairClient `account.get_account_funds` error",
                exc_info=True,
                extra={
                    "client": self.betting_client,
                    "trading_function": "account.get_account_funds",
                    "response": e,
                },
            )

    @property
    def min_bet_size(self) -> Optional[float]:
        if self.account_details:
            try:
                return currency_parameters[self.account_details.currency_code][
                    "min_bet_size"
                ]
            except KeyError:
                logger.warning(
                    "min_bet_size KeyError: %s" % self.account_details.currency_code
                )
                return MIN_BET_SIZE
            except Exception as e:
                logger.error("min_bet_size error: {0}".format(e), exc_info=True)
                return MIN_BET_SIZE
        else:
            return MIN_BET_SIZE

    @property
    def min_bet_payout(self) -> Optional[float]:
        if self.account_details:
            try:
                return currency_parameters[self.account_details.currency_code][
                    "min_bet_payout"
                ]
            except KeyError:
                logger.warning(
                    "min_bet_payout KeyError: %s" % self.account_details.currency_code
                )
                return MIN_BET_PAYOUT
            except Exception as e:
                logger.error("min_bet_payout error: {0}".format(e), exc_info=True)
                return MIN_BET_PAYOUT
        else:
            return MIN_BET_PAYOUT

    @property
    def min_bsp_liability(self) -> Optional[float]:
        if self.account_details:
            try:
                return currency_parameters[self.account_details.currency_code][
                    "min_bsp_liability"
                ]
            except KeyError:
                logger.warning(
                    "min_bsp_liability KeyError: %s"
                    % self.account_details.currency_code
                )
                return MIN_BSP_LIABILITY
            except Exception as e:
                logger.error("min_bsp_liability error: {0}".format(e), exc_info=True)
                return MIN_BSP_LIABILITY
        else:
            return MIN_BSP_LIABILITY
