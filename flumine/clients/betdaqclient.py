import logging
from typing import Optional
from .baseclient import BaseClient
from .clients import ExchangeType

from betdaq.exceptions import BetdaqError

logger = logging.getLogger(__name__)


class BetdaqClient(BaseClient):
    """
    BETDAQ betting client.
    """

    EXCHANGE = ExchangeType.BETDAQ

    def login(self) -> None:
        pass  # NR

    def keep_alive(self) -> None:
        pass  # NR

    def logout(self) -> None:
        pass  # NR

    def update_account_details(self) -> None:
        try:
            self.account_funds = self.betting_client.account.get_account_balances()
            logger.info(
                "account_funds updated",
                extra={
                    "client": repr(self.betting_client),
                    "account_funds": self.account_funds,
                },
            )
        except (BetdaqError, Exception) as e:
            logger.error(
                "BetdaqClient `account.get_account_details` error",
                exc_info=True,
                extra={
                    "client": self.betting_client,
                    "trading_function": "account.get_account_balances",
                    "response": e,
                },
            )

    def min_bet_size(self) -> Optional[float]:
        return 1

    def min_bet_payout(self) -> Optional[float]:
        return None  # todo?

    def min_bsp_liability(self) -> Optional[float]:
        return None  # XSP todo?
