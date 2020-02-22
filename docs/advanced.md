# Advanced


### Trading Client

_betfairlightweight_

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
