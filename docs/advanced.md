# Advanced

## Flumine

Functions:

- `add_worker` Adds a [worker](/advanced/#background-workers) to the framework
- `add_client_control` Adds a [client control](/advanced/#client-controls) to the framework
- `add_trading_control` Adds a [trading control](/advanced/#trading-controls) to the framework
- `add_market_middleware` Adds [market middleware](/markets/#middleware) to the framework
- `add_logging_control` Adds a [logging control](/advanced/#logging-controls) to the framework

The Flumine class can be adapted by overriding the following functions:

- `_process_market_books()` called on MarketBook event
- `_process_market_orders()` called when market has pending orders
- `_process_order_package()` called on new OrderPackage
- `_add_live_market()` called when new Market received through streams
- `_process_raw_data()` called on RawData event
- `_process_market_catalogues` called on MarketCatalogue event
- `_process_current_orders` called on currentOrders event
- `_process_custom_event` called on CustomEvent event see [here](/advanced/#custom-event)
- `_process_close_market` called on Market closure
- `_process_cleared_orders()` called on ClearedOrders event
- `_process_cleared_markets()` called on ClearedMarkets event
- `_process_end_flumine()` called on Flumine termination

## Base Strategy
### Parameters

- `market_filter` Streaming market filter required
- `market_data_filter` Streaming market data filter required
- `streaming_timeout` Streaming timeout, will call snap() on cache every x seconds
- `conflate_ms` Streaming conflate
- `stream_class` MarketStream or RawDataStream
- `name` Strategy name, if None will default to class name
- `context` Dictionary object where any extra data can be stored here such as triggers
- `max_selection_exposure` Max exposure per selection (including new order), note this does __not__ handle reduction in exposure due to laying another runner
- `max_order_exposure` Max exposure per order
- `client` Strategy client, half implemented when flumine will be migrated to multi clients

### Functions

The following functions can be overridden dependant on the strategy:

`add()` Function called when strategy is added to framework

`start()` Function called when framework starts

`check_market_book()` Function called with marketBook, `process_market_book` is only executed if this returns True

`process_market_book()` Processes market book updates, called on every update that is received

`process_raw_data()` As per `process_market_book` but handles raw data

`process_orders()` Process list of Order objects for strategy and Market

`process_closed_market()` Process Market after closure

`finish()` Function called when framework ends

`place_order()` Places an order by first validating using `validate_order`

`cancel_order()` Cancel an order

`update_order()` Updates an order

`replace_order()` Replaces an order

### Runner Context


## Streams

### Market Stream

Flumine handles market streams by taking the parameters provided in the strategies, a strategy will then subscribe to the stream. This means strategies can share streams reducing load or create new if they require different markets or data filter.

### Data Stream

Similar to Market Streams but the raw streaming data is passed back, this reduces ram/CPU and allows recording of the data for future playback, see the example marketrecorder.py

### Historical Stream

This is created on a per market basis when backtesting.

### Order Stream

_In development_

### Custom Stream

_In development_

## Custom Event

## Trading Controls

Before placing an order flumine will check the client and trading controls, this allows validation to occur before execution. If an order does not meet any of these validations it is not executed and status is updated to `Violation`.

### Client Controls

- `MaxOrderCount`: Checks order count is not over betfair transaction limit (1000) 

### Trading Controls

- `OrderValidation`: Checks order is valid (size/odds)
- `StrategyExposure`: Checks order does not go over `strategy.max_order_exposure` and `strategy.max_selection_exposure`

## Logging Controls

Custom logging is available using the `LoggingControl` class, the [base class](https://github.com/liampauling/flumine/blob/master/flumine/controls/loggingcontrols.py#L12) creates debug logs and can be used as follows:

```python
from flumine.controls.loggingcontrols import LoggingControl

control = LoggingControl()

framework.add_logging_control(control)
```

!!! tip
    More than one control can be added, for example a csv logger and db logger.

## Background Workers

By default flumine adds the following workers:
 
- `keep_alive`: runs every 1200s to make sure the client is either logged in or kept alive
- `poll_account_balance`: runs every 60s to poll account balance endpoint
- `poll_market_catalogue`: runs every 60s to poll listMarketCatalogue endpoint
- `poll_cleared_orders`: runs when closed market is added to `flumine.cleared_market_queue`

Further workers can be added as per:

```python
from flumine.worker import BackgroundWorker

def func(a): print(a)

worker = BackgroundWorker(
    interval=10, function=func, func_args=("hello",), name="print_a"
)

framework.add_worker(
    worker
)
```

## Error Handling

Flumine will catch all errors that occur in `strategy.check_market` and `strategy.process_market_book`, and log either error or critical errors.

!!! tip
    You can remove this error handling by setting `config.raise_errors = True`

## Logging

jsonlogger is used to log extra detail, see below for a typical setup:

```python
import time
import logging
from pythonjsonlogger import jsonlogger

logger = logging.getLogger()

custom_format = "%(asctime) %(levelname) %(message)"
log_handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(custom_format)
formatter.converter = time.gmtime
log_handler.setFormatter(formatter)
logger.addHandler(log_handler)
logger.setLevel(logging.INFO)
```

## Config

### hostname

Used as customerStrategyRefs so that only orders created by the running instance is returned.

### process_id

OS process id of running application.

### current_time

Used for backtesting

### current_time

Raises errors on strategy functions, see [Error Handling](/advanced/#error-handling)
