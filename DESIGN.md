# flūmine design

Betfair trading framework with a focus on:

- simplicity
- modular
- pythonic
- rock-solid
- safe


## design

Main loop (flumine)
- handles all events
- runs in __main__

Streams
- Single stream (market)
- As above but 'data' (flumine listener)
- Future work:
    - Separate threads
    - Order stream

Strategies (previously storageengine)
- Class based
- Subscribe to streams

Handles
- Stream reconnect
- Trading client login/logout
- Trading client keep alive
- Future work:
    - Execution
        - place/cancel/replace/update
        - controls
        - fillKill
    - Market Catalogue
    - Polling (scores/raceCard etc)
    - CurrentOrders / ClearedOrders
    - database connection/logging

## setup

The framework can be used as follows:

```python
from flumine import Flumine
import betfairlightweight


trading = betfairlightweight.APIClient("username")

framework = Flumine(
    client=trading,
    strategies=[],
    market_filter={},
    market_data_filter={},
)

framework.run()
```

Example strategy:

```python
from flumine import BaseStrategy


class Ex(BaseStrategy):
    def __init__(self):
        pass
        
    def process_market_book(self, market_book):
        pass
```
