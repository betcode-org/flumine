# Advanced


### Trading Client

_betfairlightweight_


### Streams

_Market Stream_

_Data Stream_

_Historical Stream_

_Order Stream_

_Custom Stream_

### Trading Controls

### Logging Controls

### Background Workers

By default flumine adds a keep_alive worker which runs every 1200s to make sure the client is either logged in or kept alive, further workers can be added:

```python
from flumine.worker import BackgroundWorker

def func(a): print(a)

worker = BackgroundWorker(
    interval=10, function=func, args=("hello",)
)

flumine.add_worker(
    worker
)
```

### Error Handling

### Logging

### Custom Polling / Streaming

### Strategies


### Flumine

The Flumine class can be adapted by overriding the following functions:


- _process_market_books called on MarketBook event
- _process_raw_data called on RawData event
- _process_end_flumine called on Flumine termination
