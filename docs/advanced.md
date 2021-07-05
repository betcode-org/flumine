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


## Streams

### Market Stream

Flumine handles market streams by taking the parameters provided in the strategies, a strategy will then subscribe to the stream. This means strategies can share streams reducing load or create new if they require different markets or data filter.

### Data Stream

Similar to Market Streams but the raw streaming data is passed back, this reduces ram/CPU and allows recording of the data for future playback, see the example marketrecorder.py

### Historical Stream

This is created on a per market basis when backtesting.

### Order Stream

Subscribes to all orders per running instance using the `config.hostname`

## Custom Event




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

### simulated

Updated to True when backtesting or paper trading

### instance_id

Store server id or similar (e.g. AWS ec2 instanceId)

### hostname

Used as customerStrategyRefs so that only orders created by the running instance are returned.

### process_id

OS process id of running application.

### current_time

Used for backtesting

### raise_errors

Raises errors on strategy functions, see [Error Handling](/advanced/#error-handling)

### max_execution_workers

Max number of workers in execution thread pool

### async_place_orders

Place orders sent with place orders flag, prevents waiting for bet delay

### place_latency

Place latency used for backtesting / simulation execution

### cancel_latency

Cancel latency used for backtesting / simulation execution

### update_latency

Update latency used for backtesting / simulation execution

### replace_latency

Replace latency used for backtesting / simulation execution

### order_sep 

customer_order_ref separator
