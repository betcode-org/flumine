# v3

v3 is a breaking change to the initialisation of the framework that allows the user to have full control over data streams and strategy subscriptions whilst removing the dependency of a Betfair client.

This means an instance can be setup to execute on either individual venues or multiple concurrently, current status:

- Betfair: Completed
- BETDAQ: Completed
- BetConnect: Development
- Polymarket: Roadmap
- Kalshi: Roadmap
- Smarkets: Roadmap
- Matchbook: Roadmap

## Breaking Changes

### Live

Historically flumine would create streams based on provided market filters however from v3 this has moved to the following design:

```python
import betfairlightweight
from flumine import Flumine, clients
from flumine.streams.betfairmarketstream import BetfairMarketStream
from betfairlightweight.filters import streaming_market_filter

# Initialize your client
trading = betfairlightweight.APIClient("username")
client = clients.BetfairClient(trading)

# Initialize the framework
framework = Flumine(client)

# Create stream(s) (market data)
stream = BetfairMarketStream(
    framework,
    market_filter=streaming_market_filter(
        event_type_ids=["7"],
        country_codes=["GB"],
        market_types=["WIN"],
    ),
)
framework.add_stream(stream)

# Add your strategy to the framework with a stream
framework.add_strategy(
    ExampleStrategy(streams=[stream])
)

# Start the trading framework
framework.run()
```

A strategy can therefore subscribe to multiple streams and a stream can be subscribed to multiple strategies, these can also be across VenueTypes. 

It is also possible to subscribe or unsubscribe after a strategy has been initialised:

```python
strategy = ExampleStrategy()
strategy.subscribe_to_stream(stream)
strategy.unsubscribe_from_stream(stream)
```

### Simulation

The simulation setup has also changed to match live:

```python
import betfairlightweight
from flumine import FlumineSimulation, clients
from flumine.streams.betfairhistoricalstream import BetfairHistoricalStream

# Initialize your client
client = clients.SimulatedClient()

# Initialize the framework
framework = FlumineSimulation(client=client)

# Create stream(s) (historic data)
stream = BetfairHistoricalStream(
    framework,
    market_filter="tests/resources/PRO-1.170258213",
    output_queue=False,
)
framework.add_stream(stream)

# Add your strategy to the framework with a stream (this can be a list)
strategy = LowestLayer(
    streams=[stream],
    max_order_exposure=1000,
    max_selection_exposure=105,
    context={"stake": 2},
)
framework.add_strategy(strategy)

# Start the trading framework
framework.run()
```

!!! note
There are no other changes to the public / exposed API of flumine in v2->v3.
