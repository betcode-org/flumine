# Advanced

## Flumine

The Flumine class can be adapted by overriding the following functions:

- `_process_market_books()` called on MarketBook event
- `_process_raw_data()` called on RawData event
- `_process_market_catalogues` called on MarketCatalogue event
- `_process_end_flumine()` called on Flumine termination

## Base Strategy
### Parameters

`market_filter` Streaming market filter required

`market_data_filter` Streaming market data filter required

`streaming_timeout` Streaming timeout, will call snap() on cache every x seconds

`conflate_ms` Streaming conflate

`stream_class` MarketStream or RawDataStream

`name` Strategy name, if None will default to class name

`context` Dictionary object where any extra data can be stored here such as triggers

### Functions

The following functions can be overridden dependant on the strategy:

`add()` Function called when strategy is added to framework

`start()` Function called when framework starts

`check_market_book()` Function called with marketBook, `process_market_book` is only executed if this returns True

`process_market_book()` Processes market book updates, called on every update that is received

`process_raw_data()` As per `process_market_book` but handles raw data

`process_race_card()` _In development_

`process_orders()` _In development_

`finish()` Function called when framework ends

## Client

Flumine uses clients to hold betting clients for example BetfairClient requires a betfairlightweight trading client, future work may allow multiple clients / different exchanges. 

### Betfair Client

### Backtest Client

!!! tip
    It is possible to handle a custom client within a strategy just watch out for blocking the main loop if you make any http requests.

## Execution

### Betfair Execution

### Backtest Execution

## Markets

Stores latest marketBook objects.

### Middleware

__In development__

Analytics / historical tick data

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

## Trading Controls

_In development_

### Client Controls

### Trading Controls

## Logging Controls

_In development_

## Background Workers

By default flumine adds the following workers:
 
- `keep_alive`: runs every 1200s to make sure the client is either logged in or kept alive
- `poll_market_catalogue`: runs every 60s to poll listMarketCatalogue endpoint


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

## Logging


## Config

### hostname

Used as customerStrategyRefs so that only orders created by the running instance is returned.

### process_id

OS process id of running application.

### current_time

Used for backtesting
