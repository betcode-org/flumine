# Clients

Flumine is capable of using multiple clients, these can be of the same `ExchangeType`, a variation depending on use case or your own custom client/wrapper. The default workers handle login/keep-alive/logout and market closure for all clients added to the framework automatically.

## ExchangeTypes

- BETFAIR: `BetfairClient`
- SIMULATED: `SimulatedClient`
- BETCONNECT: `BetconnectClient`

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
betfair_client = self.clients.get_betfair_default()

client = self.clients.get_client(ExchangeType.SIMULATED, username="123")
```

!!! tip
    `get_default` and `get_betfair_default` will use the first client added via `add_client` (ordered list)

By default a transaction will use `clients.get_default()` however you can use a particular client:

```python
client = self.clients.get_client(ExchangeType.SIMULATED, username="123")

market.place_order(order, client=client)
```

or using a transaction directly:

```python
client = self.clients.get_client(ExchangeType.SIMULATED, username="123")

with market.transaction(client=client) as t:
    t.place_order(order)
```

## Settings

- `transaction_limit` (per hour transaction limit)
- `interactive_login` (betfair interactive login)
- `username` (defaults to guid)
- `order_stream` (disable order stream)
- `best_price_execution` (only configurable when simulating)
- `username` (defaults to guid)
- `min_bet_validation` (remove min bet validation)
- `paper_trade` (simulation engine used)
- `market_recording_mode` (no order stream / workers)
- `simulated_full_match` (simulate orders matching 100% on execution)
- `execution_cls` (configure class used for executing orders)