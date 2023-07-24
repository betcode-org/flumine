# Strategies

## BaseStrategy

The base strategy class should be used for all strategies and contains the following parameters / functions for order/trade execution.

### Parameters

- `market_filter` Streaming market filter or list of filters required
- `market_data_filter` Streaming market data filter required
- `streaming_timeout` Streaming timeout, will call snap() on cache every x seconds
- `conflate_ms` Streaming conflate
- `stream_class` MarketStream or RawDataStream
- `name` Strategy name, if None will default to class name
- `context` Dictionary object where any extra data can be stored here such as triggers
- `max_selection_exposure` Max exposure per selection (including new order), note this does __not__ handle reduction in exposure due to laying another runner
- `max_order_exposure` Max exposure per order
- `clients` flumine.clients
- `max_trade_count` Max total number of trades per runner
- `max_live_trade_count` Max live (with executable orders) trades per runner
- `multi_order_trades` Allow multiple live orders per trade

### Functions

The following functions can be overridden dependent on the strategy:

- `add()` Function called when strategy is added to framework
- `start()` Function called when framework starts
- `process_added_market()` Process Market when it gets added to the framework
- `check_market_book()` Function called with marketBook, `process_market_book` is only executed if this returns True
- `process_market_book()` Processes market book updates, called on every update that is received
- `process_raw_data()` As per `process_market_book` but handles raw data
- `process_orders()` Process list of Order objects for strategy and Market
- `process_closed_market()` Process Market after closure
- `finish()` Function called when framework ends

### Runner Context

Each strategy stores a `RunnerContext` object which contains the state of a runner based on all and current active trades. This is used by controls to calculate exposure and control the number of live or total trades.

```python
runner_context = self.get_runner_context(
    market.market_id, runner.selection_id, runner.handicap
)

runner_context.live_trade_count
```
