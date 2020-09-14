import datetime


class PendingPackages(list):
    """List which only returns packages
    which haven't been processed.
    """

    def __iter__(self):
        return (x for x in list.__iter__(self) if not x.processed)


class SimulatedPlaceResponse:
    def __init__(
        self,
        status: str,
        order_status: str = None,
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
