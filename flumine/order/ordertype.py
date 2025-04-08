import betdaq
from enum import Enum
from betdaq.enums import OrderKillType, WithdrawRepriceOption
from betfairlightweight.resources.bettingresources import LineRangeInfo

from ..clients.clients import ExchangeType


class OrderTypes(Enum):
    LIMIT = "Limit"
    LIMIT_ON_CLOSE = "Limit on close"
    MARKET_ON_CLOSE = "Market on close"


class BaseOrderType:
    EXCHANGE = None
    ORDER_TYPE = None

    def place_instruction(self) -> dict:
        raise NotImplementedError

    @property
    def info(self):
        raise NotImplementedError


class LimitOrder(BaseOrderType):
    EXCHANGE = ExchangeType.BETFAIR
    ORDER_TYPE = OrderTypes.LIMIT

    def __init__(
        self,
        price: float,
        size: float = None,
        persistence_type: str = "LAPSE",
        time_in_force: str = None,
        min_fill_size: float = None,
        bet_target_type: str = None,
        bet_target_size: float = None,
        price_ladder_definition: str = "CLASSIC",
        line_range_info: LineRangeInfo = None,
    ):
        self.price = price
        self.size = size
        self.persistence_type = persistence_type
        self.time_in_force = time_in_force
        self.min_fill_size = min_fill_size
        self.bet_target_type = bet_target_type
        self.bet_target_size = bet_target_size
        self.price_ladder_definition = price_ladder_definition
        self.line_range_info = line_range_info

    def place_instruction(self) -> dict:
        return {
            "size": self.size,
            "price": self.price,
            "persistenceType": self.persistence_type,
            "timeInForce": self.time_in_force,
            "minFillSize": self.min_fill_size,
            "betTargetType": self.bet_target_type,
            "betTargetSize": self.bet_target_size,
        }

    @property
    def info(self):
        return {
            "order_type": self.ORDER_TYPE.value,
            "price": self.price,
            "size": self.size,
            "persistence_type": self.persistence_type,
            "time_in_force": self.time_in_force,
            "min_fill_size": self.min_fill_size,
            "bet_target_type": self.bet_target_type,
            "bet_target_size": self.bet_target_size,
            "price_ladder_definition": self.price_ladder_definition,
        }


class LimitOnCloseOrder(BaseOrderType):
    EXCHANGE = ExchangeType.BETFAIR
    ORDER_TYPE = OrderTypes.LIMIT_ON_CLOSE

    def __init__(
        self, liability: float, price: float, price_ladder_definition: str = "CLASSIC"
    ):
        self.liability = liability
        self.price = price
        self.price_ladder_definition = price_ladder_definition

    def place_instruction(self) -> dict:
        return {
            "liability": self.liability,
            "price": self.price,
        }

    @property
    def info(self):
        return {
            "order_type": self.ORDER_TYPE.value,
            "liability": self.liability,
            "price": self.price,
            "price_ladder_definition": self.price_ladder_definition,
        }


class MarketOnCloseOrder(BaseOrderType):
    EXCHANGE = ExchangeType.BETFAIR
    ORDER_TYPE = OrderTypes.MARKET_ON_CLOSE

    def __init__(self, liability: float):
        self.liability = liability

    def place_instruction(self) -> dict:
        return {
            "liability": self.liability,
        }

    @property
    def info(self):
        return {
            "order_type": self.ORDER_TYPE.value,
            "liability": self.liability,
        }


class BetdaqLimitOrder(BaseOrderType):
    EXCHANGE = ExchangeType.BETDAQ
    ORDER_TYPE = OrderTypes.LIMIT

    def __init__(
        self,
        price,
        size,
        betdaq_runner_id,
        runner_reset_count,
        withdrawal_sequence_number,
        kill_type=OrderKillType.FillOrKillDontCancel.value,
        fill_or_kill_threshold=0.0,
        cancel_on_in_running=True,
        cancel_if_selection_reset=True,
        withdrawal_reprice_option=WithdrawRepriceOption.Cancel.value,
    ):
        self.price = price
        self.size = size
        self.betdaq_runner_id = betdaq_runner_id
        self.runner_reset_count = runner_reset_count
        self.withdrawal_sequence_number = withdrawal_sequence_number
        self.kill_type = kill_type
        self.fill_or_kill_threshold = fill_or_kill_threshold
        self.cancel_on_in_running = cancel_on_in_running
        self.cancel_if_selection_reset = cancel_if_selection_reset
        self.withdrawal_reprice_option = withdrawal_reprice_option
        self.price_ladder_definition = None

    def place_instruction(self, polarity, ref=None) -> dict:
        return betdaq.filters.create_order(
            SelectionId=self.betdaq_runner_id,
            Stake=self.size,
            Price=self.price,
            Polarity=polarity,
            ExpectedSelectionResetCount=self.runner_reset_count,
            ExpectedWithdrawalSequenceNumber=self.withdrawal_sequence_number,
            KillType=self.kill_type,
            FillOrKillThreshold=self.fill_or_kill_threshold,
            CancelOnInRunning=self.cancel_on_in_running,
            CancelIfSelectionReset=self.cancel_if_selection_reset,
            WithdrawalRepriceOption=self.withdrawal_reprice_option,
            PunterReferenceNumber=ref,
        )

    @property
    def info(self):
        return {
            "order_type": self.ORDER_TYPE,
            "price": self.price,
            "size": self.size,
            "betdaq_runner_id": self.betdaq_runner_id,
            "runner_reset_count": self.runner_reset_count,
            "withdrawal_sequence_number": self.withdrawal_sequence_number,
            "kill_type": self.kill_type,
            "fill_or_kill_threshold": self.fill_or_kill_threshold,
            "cancel_on_in_running": self.cancel_on_in_running,
            "cancel_if_selection_reset": self.cancel_if_selection_reset,
            "withdrawal_reprice_option": self.withdrawal_reprice_option,
        }
