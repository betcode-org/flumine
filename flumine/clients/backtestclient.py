from betfairlightweight.resources.accountresources import AccountDetails

from .baseclient import BaseClient
from .clients import ExchangeType


class BacktestClient(BaseClient):
    """
    Backtest betting client.
    """

    EXCHANGE = ExchangeType.BACKTEST
    DISCOUNT_RATE = 0
    CURRENCY_CODE = "GBP"

    def login(self) -> None:
        return

    def keep_alive(self) -> None:
        return

    def logout(self) -> None:
        return

    def update_account_details(self) -> None:
        self.account_details = AccountDetails(
            **{"discountRate": self.DISCOUNT_RATE, "currencyCode": self.CURRENCY_CODE}
        )
