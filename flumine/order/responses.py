import datetime
from typing import Optional


class Responses:
    """Order responses"""

    def __init__(self):
        self.date_time_created = datetime.datetime.utcnow()
        self.current_order = None  # resources.CurrentOrder
        self.place_response = None  # resources.PlaceOrderInstructionReports
        self.cancel_responses = []
        self.replace_responses = []
        self.update_responses = []
        self._date_time_placed = None

    def placed(self, response=None, dt: bool = True) -> None:
        if response:
            self.place_response = response
        if dt:
            self._date_time_placed = datetime.datetime.utcnow()

    def cancelled(self, response) -> None:
        self.cancel_responses.append(response)

    def replaced(self, response) -> None:
        self.replace_responses.append(response)

    def updated(self, response) -> None:
        self.update_responses.append(response)

    @property
    def date_time_placed(self) -> Optional[datetime.datetime]:
        if self._date_time_placed:
            return self._date_time_placed
        elif self.current_order:
            try:
                return self.current_order.placed_date
            except AttributeError:
                return
