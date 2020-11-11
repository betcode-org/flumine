# Markets

## Market

Within markets you have market objects which contains current up to date market data.

### Class variables

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

### Middleware

It is common that you want to carry about analysis on a market before passing through to strategies, similar to Django's middleware design flumine allows middleware to be executed.

For example backtesting uses [simulated middleware](https://github.com/liampauling/flumine/blob/master/flumine/markets/middleware.py#L15) in order to calculate order matching.

!!! note
    Middleware will be executed in the order it is added and before the strategies are processed.
