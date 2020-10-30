import csv
import logging
from flumine.controls.loggingcontrols import LoggingControl

logger = logging.getLogger(__name__)

FIELDNAMES = [
    "bet_id",
    "strategy_name",
    "market_id",
    "selection_id",
    "trade_id",
    "date_time_placed",
    "price",
    "price_matched",
    "size",
    "size_matched",
    "profit",
    "side",
    "elapsed_seconds_executable",
    "order_status",
    "market_note",
    "notes",
]


class BacktestLoggingControl(LoggingControl):
    NAME = "BACKTEST_LOGGING_CONTROL"

    def __init__(self, *args, **kwargs):
        super(BacktestLoggingControl, self).__init__(*args, **kwargs)
        self._setup()

    def _setup(self):
        with open("orders.txt", "w") as m:
            csv_writer = csv.DictWriter(m, delimiter=",", fieldnames=FIELDNAMES)
            csv_writer.writeheader()

    def _process_cleared_orders_meta(self, event):
        orders = event.event
        with open("orders.txt", "a") as m:
            for order in orders:
                try:
                    order_data = {
                        "bet_id": order.bet_id,
                        "strategy_name": order.trade.strategy,
                        "market_id": order.market_id,
                        "selection_id": order.selection_id,
                        "trade_id": order.trade.id,
                        "date_time_placed": order.responses.date_time_placed,
                        "price": order.order_type.price,
                        "price_matched": order.average_price_matched,
                        "size": order.order_type.size,
                        "size_matched": order.size_matched,
                        "profit": order.simulated.profit,
                        "side": order.side,
                        "elapsed_seconds_executable": order.elapsed_seconds_executable,
                        "order_status": order.status.value,
                        "market_note": order.trade.market_notes,
                        "notes": order.trade.notes_str,
                    }
                    csv_writer = csv.DictWriter(
                        m, delimiter=",", fieldnames=FIELDNAMES
                    )
                    csv_writer.writerow(order_data)
                except Exception as e:
                    print("error", e)

        logger.info("Orders updated", extra={"order_count": len(orders)})
