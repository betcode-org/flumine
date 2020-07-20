from typing import Optional
from betfairlightweight.metadata import transaction_limit as betfair_transaction_limit

from ..utils import create_short_uuid
from .clients import ExchangeType

DEFAULT_CAPITAL_BASE = 0
DEFAULT_COMMISSION_BASE = 0.05


class BaseClient:
    """
    Abstraction of betting client.
    """

    EXCHANGE = None

    def __init__(
        self,
        betting_client=None,
        transaction_limit: Optional[int] = betfair_transaction_limit,
        capital_base: int = DEFAULT_CAPITAL_BASE,
        commission_base: float = DEFAULT_COMMISSION_BASE,
        interactive_login: bool = False,
        id_: str = None,
        order_stream: bool = True,
        best_price_execution: bool = True,
        paper_trade: bool = False,
    ):
        self.id = id_ or create_short_uuid()
        self.betting_client = betting_client
        self.transaction_limit = transaction_limit
        self.capital_base = capital_base
        self.commission_base = commission_base
        self.interactive_login = interactive_login
        self.order_stream = order_stream
        self.best_price_execution = best_price_execution
        self.paper_trade = paper_trade

        self.account_details = None
        self.account_funds = None
        self.commission_paid = 0
        self.chargeable_transaction_count = 0

        self.execution = None  # set during flumine init
        self.trading_controls = []

    def login(self) -> None:
        raise NotImplementedError

    def keep_alive(self) -> None:
        raise NotImplementedError

    def logout(self) -> None:
        raise NotImplementedError

    def update_account_details(self) -> None:
        raise NotImplementedError

    def add_execution(self, flumine) -> None:
        if self.EXCHANGE == ExchangeType.SIMULATED or self.paper_trade:
            self.execution = flumine.simulated_execution
        elif self.EXCHANGE == ExchangeType.BETFAIR:
            self.execution = flumine.betfair_execution

    @property
    def min_bet_size(self) -> Optional[float]:
        raise NotImplementedError

    @property
    def min_bet_payout(self) -> Optional[float]:
        raise NotImplementedError

    @property
    def min_bsp_liability(self) -> Optional[float]:
        raise NotImplementedError

    @property
    def info(self) -> dict:
        return {
            "id": self.id,
            "exchange": self.EXCHANGE.value if self.EXCHANGE else None,
            "betting_client": self.betting_client,
            "chargeable_transaction_count": self.chargeable_transaction_count,
            "trading_controls": self.trading_controls,
            "order_stream": self.order_stream,
            "best_price_execution": self.best_price_execution,
            "paper_trade": self.paper_trade,
        }
