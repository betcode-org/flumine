# Workers

## Background Workers

Background workers run in their own thread allowing cleanup / cron like workers to run in the background, by default flumine adds the following workers:

- `keep_alive`: runs every 1200s (or session_timeout/2) to make sure the client is either logged in or kept alive
- `poll_account_balance`: runs every 120s to poll account balance endpoint
- `poll_market_catalogue`: runs every 60s to poll listMarketCatalogue endpoint
- `poll_market_closure`: checks for closed markets to get cleared orders at order and market level

## Custom Workers

Further workers can be added as per:

```python
from flumine.worker import BackgroundWorker

def func(context: dict, flumine, name=""):
    print(name)

    
worker = BackgroundWorker(
    framework, interval=10, function=func, func_args=("hello",)
)

framework.add_worker(
    worker
)
```
