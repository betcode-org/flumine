import datetime
from typing import Optional


class RunnerContext:
    """Runner context at strategy level"""

    def __init__(self, selection_id: int):
        self.selection_id = selection_id
        self.invested = False
        self.datetime_last_placed = None
        self.datetime_last_reset = None
        self.trade_count = 0
        self.live_trade_count = 0

    def place(self) -> None:
        self.invested = True
        self.datetime_last_placed = datetime.datetime.utcnow()
        self.trade_count += 1
        self.live_trade_count += 1

    def reset(self) -> None:
        self.datetime_last_reset = datetime.datetime.utcnow()
        self.live_trade_count -= 1

    @property
    def executable_orders(self) -> bool:
        if self.live_trade_count:
            return True
        else:
            return False

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
