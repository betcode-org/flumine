# Clients

Flumine is capable of using multiple clients, these can be of the same `ExchangeType`, a variation depending on use case or your own custom client/wrapper. The default workers handle login/keep-alive/logout and market closure for all clients added to the framework automatically.

## ExchangeTypes

- BETFAIR: `BetfairClient`
- SIMULATED: `SimulatedClient`
- BETCONNECT: `BetconnectClient`

## Strategy use

To add a client use the `add_client` this will allow strategies to use them via `framework.clients` or `strategy.clients`

```python
from flumine import Flumine, clients

framework = Flumine()

client = clients.SimulatedClient(username="123")
framework.add_client(client)
```

To access clients within a strategy use the helper functions:

```python
betfair_client = self.clients.get_betfair_default()

client = self.clients.get_client(ExchangeType.SIMULATED, username="123")
```

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
