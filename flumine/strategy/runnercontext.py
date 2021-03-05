import logging
import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class RunnerContext:
    """Runner context at strategy level"""

    def __init__(self, selection_id: int):
        self.selection_id = selection_id
        self.invested = False
        self.datetime_last_placed = None
        self.datetime_last_reset = None
        self.trades = []
        self.live_trades = []

    def place(self, trade_id) -> None:
        self.invested = True
        self.datetime_last_placed = datetime.datetime.utcnow()
        if trade_id not in self.trades:
            self.trades.append(trade_id)
        if trade_id not in self.live_trades:
            self.live_trades.append(trade_id)

    def reset(self, trade_id) -> None:
        self.datetime_last_reset = datetime.datetime.utcnow()
        try:
            self.live_trades.remove(trade_id)
        except ValueError:
            logger.warning(
                "Trade '%s' not present in RunnerContext live_trades on reset"
                % trade_id
            )

    @property
    def executable_orders(self) -> bool:
        if self.live_trades:
            return True
        else:
            return False

    @property
    def trade_count(self) -> int:
        return len(self.trades)

    @property
    def live_trade_count(self) -> int:
        return len(self.live_trades)

    @property
    def placed_elapsed_seconds(self) -> Optional[float]:
        if self.datetime_last_placed:
            return (
                datetime.datetime.utcnow() - self.datetime_last_placed
            ).total_seconds()

    @property
    def reset_elapsed_seconds(self) -> Optional[float]:
        if self.datetime_last_reset:
            return (
                datetime.datetime.utcnow() - self.datetime_last_reset
            ).total_seconds()
