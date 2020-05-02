# Trades / Orders

## Trade

A trade object is used to handle order execution.

```python
from flumine.order.trade import Trade
from flumine.order.ordertype import LimitOrder

trade = Trade(
    market_id="1.2345678",
    selection_id=123456,
    strategy=strategy
)
trade.orders  # []
trade.status  # todo

order = trade.create_order(
    side="LAY",
    order_type=LimitOrder(price=1.01, size=2.00)
)
trade.orders  # [<BetfairOrder>]
```

Extras include:

### offset orders

desc

```python
example
```

### fill kill
### greening

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
