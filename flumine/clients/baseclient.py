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
        username: str = None,
        order_stream: bool = True,
        best_price_execution: bool = True,
        min_bet_validation: bool = True,
        paper_trade: bool = False,
        market_recording_mode: bool = False,
    ):
        if hasattr(betting_client, "lightweight"):
            assert (
                betting_client.lightweight is False
            ), "flumine requires resources, please set lightweight to False"
        self._username = username or create_short_uuid()
        self.betting_client = betting_client
        self.transaction_limit = transaction_limit
        self.capital_base = capital_base
        self.commission_base = commission_base
        self.interactive_login = interactive_login
        self.order_stream = order_stream
        self.best_price_execution = best_price_execution
        self.min_bet_validation = min_bet_validation  # used in OrderValidation control
        self.paper_trade = paper_trade
        self.market_recording_mode = market_recording_mode

        self.account_details = None
        self.account_funds = None
        self.commission_paid = 0

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

    def add_transaction(self, count: int, failed: bool = False) -> None:
        for control in self.trading_controls:
            if hasattr(control, "add_transaction"):
                control.add_transaction(count, failed)

    @property
    def username(self) -> str:
        if self.betting_client:
            return self.betting_client.username
        else:
            return self._username

    @property
    def current_transaction_count_total(self) -> Optional[int]:
        # current hours total transaction count
        for control in self.trading_controls:
            if control.NAME == "MAX_TRANSACTION_COUNT":
                return control.current_transaction_count_total

    @property
    def transaction_count_total(self) -> Optional[int]:
        # total transaction count
        for control in self.trading_controls:
            if control.NAME == "MAX_TRANSACTION_COUNT":
                return control.transaction_count_total

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
            "username": self.username,
            "exchange": self.EXCHANGE.value if self.EXCHANGE else None,
            "betting_client": self.betting_client,
            "current_transaction_count_total": self.current_transaction_count_total,
            "transaction_count_total": self.transaction_count_total,
            "trading_controls": self.trading_controls,
            "order_stream": self.order_stream,
            "best_price_execution": self.best_price_execution,
            "paper_trade": self.paper_trade,
        }
