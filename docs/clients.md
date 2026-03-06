# Clients

Flumine is capable of using multiple clients, these can be of the same `VenueType`, a variation depending on use case or your own custom client/wrapper. The default workers handle login/keep-alive/logout and market closure for all clients added to the framework automatically.

## VenueType

- BETFAIR: `BetfairClient`
- SIMULATED: `SimulatedClient`
- BETCONNECT: `BetconnectClient`
- BETDAQ: `BETDAQ`
- SMARKETS: `Smarkets`
- MATCHBOOK: `Matchbook`
- POLYMARKET: `Polymarket`
- KALSHI: `Kalshi`

## Strategy use

To add a client use the `add_client` this will allow use via `framework.clients` or `strategy.clients`

```python
from flumine import Flumine, clients

framework = Flumine()

client = clients.BetfairClient(trading)
framework.add_client(client)
```

or when simulating:

```python
from flumine import FlumineSimulation, clients

framework = FlumineSimulation()

client = clients.SimulatedClient(username="123")
framework.add_client(client)
```

To access clients within a strategy use the helper functions:

```python
betfair_client = self.clients.get_default(VenueType.BETFAIR)

client = self.clients.get_client(VenueType.SIMULATED, username="123")
```

!!! tip
    `get_default` will use the first client added via `add_client` (ordered list) per Venue

By default a transaction will use `clients.get_default()` however you can use a particular client:

```python
client = self.clients.get_client(VenueType.SIMULATED, username="123")

market.place_order(order, client=client)
```

or using a transaction directly:

```python
client = self.clients.get_client(VenueType.SIMULATED, username="123")

with market.transaction(client=client) as t:
    t.place_order(order)
```

## Settings

- `betting_client` (venue specific betting client)
- `transaction_limit` (per hour transaction limit)
- `capital_base` (default capital)
- `commission_base` (default commission)
- `interactive_login` (betfair interactive login)
- `username` (defaults to guid)
- `order_stream` (disable order stream)
- `order_stream_conflate_ms` (conflate order stream)
- `best_price_execution` (only configurable when simulating)
- `min_bet_validation` (remove min bet validation)
- `paper_trade` (simulation engine used)
- `market_recording_mode` (no order stream / workers)
- `simulated_full_match` (simulate orders matching 100% on execution)
- `execution_cls` (configure class used for executing orders)
- `order_stream_cls` (configure class used for receiving orders)
