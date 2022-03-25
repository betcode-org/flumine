from typing import Optional
from betfairlightweight.metadata import currency_parameters
from betfairlightweight.resources.accountresources import AccountDetails

from .baseclient import BaseClient
from .clients import ExchangeType


class SimulatedClient(BaseClient):
    """
    Simulated betting client.
    """

    EXCHANGE = ExchangeType.SIMULATED
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

    @property
    def min_bet_size(self) -> Optional[float]:
        if self.account_details:
            return currency_parameters[self.account_details.currency_code][
                "min_bet_size"
            ]

    @property
    def min_bsp_liability(self) -> Optional[float]:
        if self.account_details:
            return currency_parameters[self.account_details.currency_code][
                "min_bsp_liability"
            ]

    @property
    def min_bet_payout(self) -> Optional[float]:
        if self.account_details:
            return currency_parameters[self.account_details.currency_code][
                "min_bet_payout"
            ]
