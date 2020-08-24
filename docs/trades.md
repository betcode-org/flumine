# Trades / Orders

## Trade

A trade object is used to handle order execution.

```python
from flumine.order.trade import Trade
from flumine.order.ordertype import LimitOrder

trade = Trade(
    market_id="1.2345678",
    selection_id=123456,
    handicap=1.0,
    strategy=strategy
)
trade.orders  # []
trade.status  # TradeStatus.LIVE

order = trade.create_order(
    side="LAY",
    order_type=LimitOrder(price=1.01, size=2.00)
)
trade.orders  # [<BetfairOrder>]
```

### Parameters

- `market_id` Market Id
- `selection_id` Selection Id
- `handicap` Runner handicap
- `strategy` Strategy object
- `notes` Trade notes, used to store market / trigger info for later analysis
- `fill_kill` Not implemented
- `offset` Not implemented
- `green` Not implemented
- `place_reset_seconds` Seconds to wait since `runner_context.reset` before allowing another order
- `reset_seconds` Seconds to wait since `runner_context.place` before allowing another order

### custom
You can create your own trade classes and then handle the logic within the `strategy.process_orders` function.

## Order

Order objects store all order data locally allowing trade logic to be applied.

```python
from flumine.order.order import BetfairOrder, LimitOrder

order = BetfairOrder(
    trade=trade,
    side="LAY",
    order_type=LimitOrder(price=1.01, size=2.00)
)

order.status  # OrderStatus.PENDING
order.executable()
order.execution_complete()
```
