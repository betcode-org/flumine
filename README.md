<p align="center">
  <a href="https://github.com/betcode-org">
    <img src="docs/images/logo-full.png" title="betcode-org">
  </a>
</p>

# flūmine

![Build Status](https://github.com/betcode-org/flumine/actions/workflows/test.yml/badge.svg) [![Coverage Status](https://coveralls.io/repos/github/liampauling/flumine/badge.svg?branch=master)](https://coveralls.io/github/liampauling/flumine?branch=master) [![PyPI version](https://badge.fury.io/py/flumine.svg)](https://pypi.python.org/pypi/flumine) [![Downloads](https://pepy.tech/badge/flumine)](https://pepy.tech/project/flumine)

Betting trading framework with a focus on:

- simplicity
- modular
- pythonic
- rock-solid
- safe

![Backtesting Analysis](docs/images/jupyterloggingcontrol-screenshot.png?raw=true "Jupyter Logging Control Screenshot")

Support for market, order and custom streaming data.

[docs](https://betcode-org.github.io/flumine/)

[join betcode slack group](https://join.slack.com/t/betcode-org/shared_invite/zt-h0ato238-PPbfU_T7Ji0ORjz0ESIJkg)

Tested on Python 3.7, 3.8, 3.9, 3.10 and 3.11.

## installation

```
$ pip install flumine
```

flumine requires Python 3.7+

## setup

Get started...

```python
import betfairlightweight
from flumine import Flumine, clients

trading = betfairlightweight.APIClient("username")
client = clients.BetfairClient(trading)

framework = Flumine(
    client=client,
)
```

Example strategy:

```python
from flumine import BaseStrategy
from flumine.order.trade import Trade
from flumine.order.order import LimitOrder, OrderStatus
from flumine.markets.market import Market
from betfairlightweight.filters import streaming_market_filter
from betfairlightweight.resources import MarketBook


class ExampleStrategy(BaseStrategy):
    def start(self) -> None:
        print("starting strategy 'ExampleStrategy'")

    def check_market_book(self, market: Market, market_book: MarketBook) -> bool:
        # process_market_book only executed if this returns True
        if market_book.status != "CLOSED":
            return True

    def process_market_book(self, market: Market, market_book: MarketBook) -> None:
        # process marketBook object
        for runner in market_book.runners:
            if runner.status == "ACTIVE" and runner.last_price_traded < 1.5:
                trade = Trade(
                    market_id=market_book.market_id, 
                    selection_id=runner.selection_id,
                    handicap=runner.handicap,
                    strategy=self
                )
                order = trade.create_order(
                    side="LAY", 
                    order_type=LimitOrder(price=1.01, size=2.00)
                )
                market.place_order(order)

    def process_orders(self, market: Market, orders: list) -> None:
        for order in orders:
            if order.status == OrderStatus.EXECUTABLE:
                if order.size_remaining == 2.00:
                    market.cancel_order(order, 0.02)  # reduce size to 1.98
                if order.order_type.persistence_type == "LAPSE":
                    market.update_order(order, "PERSIST")
                if order.size_remaining > 0:
                    market.replace_order(order, 1.02)  # move


strategy = ExampleStrategy(
    market_filter=streaming_market_filter(
        event_type_ids=["7"],
        country_codes=["GB"],
        market_types=["WIN"],
    )
)

framework.add_strategy(strategy)
```

Run framework:

```python
framework.run()
```

## Features

- Streaming
- Multiple strategies
- Multiple clients
- Order execution
- Paper trading
- Simulation
- Event simulation (multi market)
- Middleware and background workers to enable Scores / RaceCard / InPlayService

## Dependencies

flumine relies on these libraries:

* `betfairlightweight` - Betfair API support
* `tenacity` - Used for connection retrying (streaming)
* `python-json-logger` - JSON logging
* `requests` - HTTP support
