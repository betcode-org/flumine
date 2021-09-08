# Markets

## Market

Within markets you have market objects which contains current up to date market data.

### Class variables

- `flumine` Framework
- `market_id` MarketBook id
- `closed` Closed bool
- `date_time_closed` Closed datetime
- `market_book` Latest MarketBook object
- `market_catalogue` Latest MarketCatalogue object
- `context` Market context, store market specific context e.g. simulated data store
- `blotter` Holds all order data and position

### Functions

- `place_order(order)` Place new order from order object
- `cancel_order(order, size_reduction)` Cancel order
- `update_order(order, new_persistance_type)` Update order
- `replace_order(order, new_price)` Replace order

### Properties

- `event` Dictionary containing all event related markets (assumes markets have been subscribed)
- `event_type_id` Betfair event type id (horse racing: 7)
- `event_id` Market event id (12345)
- `market_type` Market type ('WIN')
- `seconds_to_start` Seconds to scheduled market start time (123.45)
- `elapsed_seconds_closed` Seconds since market was closed (543.21)
- `market_start_datetime` Market scheduled start time

## Transaction

The transaction class is used by default when orders are executed, however it is possible to control the execution behaviour using the transaction class like so:

```python
with market.transaction() as t:
    market.place_order(order)  # executed immediately in separate transaction
    t.place_order(order)  # executed on transaction __exit__

with market.transaction() as t:
    t.place_order(order)
    ..
    t.execute()  # above order executed
    ..
    t.cancel_order(order)
    t.place_order(order)  # both executed on transaction __exit__
```

## Blotter

The blotter is a simple and fast class to hold all orders for a particular market.

### Functions

- `strategy_orders(strategy)` Returns all orders related to a strategy
- `strategy_selection_orders(strategy, selection_id, handicap)` Returns all orders related to a strategy selection
- `selection_exposure(strategy, lookup)` Returns strategy/selection exposure

### Properties

- `live_orders` List of live orders
- `has_live_orders` Bool on live orders

## Middleware

It is common that you want to carry about analysis on a market before passing through to strategies, similar to Django's middleware design flumine allows middleware to be executed.

For example backtesting uses [simulated middleware](https://github.com/liampauling/flumine/blob/master/flumine/markets/middleware.py#L15) in order to calculate order matching.

!!! note
    Middleware will be executed in the order it is added and before the strategies are processed.

Please see below for the example middleware class if you wish to create your own:

```python
from flumine.markets.middleware import Middleware

class CustomMiddleware(Middleware):
    def __call__(self, market) -> None:
        pass  # called on each MarketBook update

    def add_market(self, market) -> None:
        print("market {0} added".format(market.market_id))

    def remove_market(self, market) -> None:
        print("market {0} removed".format(market.market_id))
```

The above middleware can then be added to the framework:

```python
framework.add_logging_control(CustomMiddleware())
```
