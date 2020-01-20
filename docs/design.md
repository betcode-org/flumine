# Design

### Main loop

Typical to most trading frameworks flumine uses an event driven design with the main thread handling these events through a FIFO [queue](https://docs.python.org/3/library/queue.html).

- handles all events in order one by one
- runs in __main__

Events:

- `MARKET_CATALOGUE` Betfair MarketCatalogue object
- `MARKET_BOOK` Betfair MarketBook object
- `CURRENT_ORDERS` Betfair CurrentOrders object
- `CLEARED_MARKETS` Betfair ClearedMarkets object
- `CLEARED_ORDERS` Betfair ClearedOrders object

___

- `CLOSE_MARKET` flumine Close Market update
- `STRATEGY_RESET` flumine Strategy Reset update
- `CLOSE_MARKET` flumine Close Market update
- `CUSTOM_EVENT` flumine Custom event update
- `NEW_DAY` flumine New Day update
- `END_FLUMINE` flumine End instance update

The above events are handled in the [flumine class]()

### Streams
- Single stream (market)
- As above but 'data' (flumine listener)
- Future work:
    - Separate threads
    - Order stream

### Strategies (previously storageengine)
- Class based
- Subscribe to streams

### Handles
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
