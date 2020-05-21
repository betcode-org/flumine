import os
import csv

from flumine import BaseStrategy
from flumine.utils import get_price

HEADERS = [
    "market_id",
    "publish_time",
    "status",
    "inplay",
    "selection_id",
    "last_price_traded",
    "back",
    "lay",
]


class PriceRecorder(BaseStrategy):
    """
    Example strategy for recording prices
    from historical or live data.
    """

    def __init__(self, *args, **kwargs):
        BaseStrategy.__init__(self, *args, **kwargs)
        self.local_dir = self.context.get("local_dir", "/tmp")
        self.filename = self.context.get("filename", "output.txt")
        self.file_directory = os.path.join(self.local_dir, self.filename)

    def add(self) -> None:
        # check local dir
        if not os.path.isdir(self.local_dir):
            raise OSError("File dir %s does not exist" % self.local_dir)
        # write headers
        with open(self.file_directory, "w") as f:
            writer = csv.DictWriter(f, fieldnames=HEADERS)
            writer.writeheader()

    def check_market_book(self, live_market, market_book):
        return True

    def process_market_book(self, live_market, market_book):
        with open(self.file_directory, "a") as f:
            writer = csv.DictWriter(f, fieldnames=HEADERS)
            for runner in market_book.runners:
                writer.writerow(
                    {
                        "market_id": market_book.market_id,
                        "publish_time": market_book.publish_time,
                        "status": market_book.status,
                        "inplay": market_book.inplay,
                        "selection_id": runner.selection_id,
                        "last_price_traded": runner.last_price_traded,
                        "back": get_price(runner.ex.available_to_back, 0),
                        "lay": get_price(runner.ex.available_to_lay, 0),
                    }
                )
