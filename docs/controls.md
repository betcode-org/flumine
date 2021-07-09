# Controls

## Trading Controls

Before placing an order flumine will check the client and trading controls, this allows validation to occur before execution. If an order does not meet any of these validations it is not executed and status is updated to `Violation`.

### Client Controls

- `MaxTransactionCount`: Checks transaction count is not over betfair transaction limit (5000 per hour) 

### Trading Controls

- `OrderValidation`: Checks order is valid (size/odds)
- `StrategyExposure`: Checks order does not invalidate `strategy.validate_order`, `strategy.max_order_exposure` or `strategy.max_selection_exposure`

### Skipping Controls

Sometimes it is desirable to skip the controls, for example when canceling an open order even if the transaction count has already reached the betfair transaction limit. This can be done by passing `force=True` when placing or changing an order:

```py
market.place_order(order, force=True)
transaction.place_order(order, force=True)
```

This works for markets and transactions and is supported by the operations `place_order`, `cancel_order`, `update_order`, and `replace_order`.

## Logging Controls

Custom logging is available using the `LoggingControl` class, the [base class](https://github.com/liampauling/flumine/blob/master/flumine/controls/loggingcontrols.py#L12) creates debug logs and can be used as follows:

```python
from flumine.controls.loggingcontrols import LoggingControl

control = LoggingControl()

framework.add_logging_control(control)
```

!!! tip
    More than one control can be added, for example a csv logger and db logger.
