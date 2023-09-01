# Performance

Flumine is heavily optimised out of the box to be as quick as possible however there are various ways to improve the performance further with minimal effort.

## Simulation

### Listener Kwargs

This is one of the most powerful options available as the variables are passed down to betfairlightweight limiting the number of updates to process, examples:

#### 600s before scheduled start and no inplay

```python
strategy = ExampleStrategy(
    market_filter={
        "markets": ["/tmp/marketdata/1.170212754"],
        "listener_kwargs": {"seconds_to_start": 600, "inplay": False},
    }
)
```

#### inplay only

```python
strategy = ExampleStrategy(
    market_filter={
        "markets": ["/tmp/marketdata/1.170212754"],
        "listener_kwargs": {"inplay": True},
    }
)
```

### Logging

Logging in python can add a lot of function calls, it is therefore recommended to switch it off once you are comfortable with the outputs from a strategy:

```python
logger.setLevel(logging.CRITICAL)
```

### File location

Flumine uses [`smart_open`](https://github.com/RaRe-Technologies/smart_open) to open historical files, so you can read files directly from s3 (`s3://http://s3.amazonaws.com/example/1.1234567`).

This might sound obvious but having the market files stored locally on your machine will allow much quicker processing. A common pattern is to use s3 to store all market files but a local cache for common markets processed.

### Betfair Historical Data

Sometimes a download from the betfair site will include market and event files in the same directory resulting in duplicate processing, flumine will log a warning on this but it is worth checking if you are seeing slow processing times.

### Multiprocessing

Simulation is CPU bound so can therefore be improved through the use of multiprocessing, threading offers no improvement due to the limitations of the GIL.

The multiprocessing example code below will:

- run a process per core
- each `run_process` will process 8 markets at a time (prevents memory leaks)
- will wait for all results before completing

```python
import os
import math
import smart_open
from concurrent import futures
from unittest.mock import patch as mock_patch
from flumine import FlumineSimulation, clients, utils
from strategies.lowestlayer import LowestLayer


def run_process(markets):
    client = clients.SimulatedClient()
    framework = FlumineSimulation(client=client)
    strategy = LowestLayer(
        market_filter={"markets": markets},
        context={"stake": 2},
    )
    with mock_patch("builtins.open", smart_open.open):
        framework.add_strategy(strategy)
        framework.run()


if __name__ == "__main__":
    all_markets = [...]
    processes = os.cpu_count()
    markets_per_process = 8  # optimal

    _process_jobs = []
    with futures.ProcessPoolExecutor(max_workers=processes) as p:
        chunk = min(
            markets_per_process, math.ceil(len(all_markets) / processes)
        )
        for m in (utils.chunks(all_markets, chunk)):
            _process_jobs.append(
                p.submit(
                    run_process,
                    markets=m,
                )
            )
        for job in futures.as_completed(_process_jobs):
            job.result()  # wait for result
```

!!! tip
    If the code above is failing add logging to the `run_process` function to find the error or run the strategy in a single process with logging

### Strategy

The heaviest load on CPU comes from reading the files and processing into py objects before processing through flumine, after this the bottleneck becomes the number of orders that need to be processed. Therefore anything that can be done to limit the number of redundant or control blocked orders will see an improvement.

### cprofile

Profiling code is always the best option for finding improvements, `cprofilev` is a commonly used python library for this:

```bash
python -m cprofilev examples/simulate.py
```

### Middleware

If you don't need the simulation middleware remove it from `framework._market_middleware`, this is useful when processing markets for data collection. This can dramatically improve processing time due to the heavy functions contained in the simulation logic.

### Libraries

Installing betfairlightweight[speed] will have a big impact on processing speed due to the inclusion of C and Rust libraries for datetime and json decoding.

## Live

For improving live trading 'Strategy' and 'cprofile' tips above will help although CPU load tends to be considerably lower compared to simulating.
