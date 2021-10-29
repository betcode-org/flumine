import datetime
from contextlib import contextmanager

from .. import config


class NewDateTime(datetime.datetime):
    @classmethod
    def utcnow(cls):
        return config.current_time


class SimulatedDateTime:
    def __init__(self):
        self._real_datetime = None

    def __call__(self, pt: datetime.datetime):
        config.current_time = pt

    def reset_real_datetime(self):
        config.current_time = self._real_datetime.utcnow()

    @contextmanager
    def real_time(self):
        datetime.datetime = self._real_datetime
        try:
            yield datetime.datetime
        finally:
            datetime.datetime = NewDateTime

    def __enter__(self):
        config.current_time = datetime.datetime.utcnow()
        self._real_datetime = datetime.datetime
        datetime.datetime = NewDateTime
        return datetime.datetime

    def __exit__(self, exc_type, exc_val, exc_tb):
        datetime.datetime = self._real_datetime


class SimulatedPlaceResponse:
    def __init__(
        self,
        status: str,  # SUCCESS, FAILURE or TIMEOUT
        order_status: str = None,  # PENDING, EXECUTION_COMPLETE, EXECUTABLE or EXPIRED
        bet_id: str = None,
        average_price_matched: float = None,
        size_matched: float = None,
        placed_date: datetime = None,
        error_code: str = None,
    ):
        self.status = status
        self.order_status = order_status
        self.bet_id = bet_id
        self.average_price_matched = average_price_matched
        self.size_matched = size_matched
        self.placed_date = placed_date
        self.error_code = error_code


class SimulatedCancelResponse:
    def __init__(
        self,
        status: str,
        size_cancelled: float = None,
        cancelled_date: datetime = None,
        error_code: str = None,
    ):
        self.status = status
        self.size_cancelled = size_cancelled
        self.cancelled_date = cancelled_date
        self.error_code = error_code


class SimulatedUpdateResponse:
    def __init__(
        self,
        status: str = None,
        error_code: str = None,
    ):
        self.status = status
        self.error_code = error_code
