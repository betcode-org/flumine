# Clients / Execution

## Live - Betfair

When using the `BetfairClient` flumine will default to using the integrated `BetfairExecution` class, this class can handle:

- `placeOrders`
- `cancelOrders`
- `updateOrders`
- `replaceOrders`

## Simulated

The `BacktestClient` will use the `SimulatedExecution` class and can be used for backtesting or paper trading where order matching is handled locally.

In development.

## Custom

Custom execution can be applied by creating your own client/overriding the `add_execution` function like so:

```python
from flumine.execution.baseexecution import BaseExecution
from flumine.clients.baseclient import BaseClient


class PrinterExecution(BaseExecution):
    def execute_place(self, order_package, http_session):
        print("execute_place")

    def execute_cancel(self, order_package, http_session):
        print("execute_cancel")

    def execute_update(self, order_package, http_session):
        print("execute_update")

    def execute_replace(self, order_package, http_session):
        print("execute_replace")


class PrinterClient(BaseClient):
    def login(self):
        return

    def keep_alive(self):
        return

    def logout(self):
        return

    def add_execution(self, flumine):
        self.execution = PrinterExecution(flumine)

    @property
    def min_bet_size(self):
        return 2.0

    @property
    def min_bet_payout(self):
        return 10.0

    @property
    def min_bsp_liability(self):
        return 10.0


client = PrinterClient()
```

!!! tip
    This can be used to handle other exchanges (betdaq) or API's that flumine cannot currently handle.
