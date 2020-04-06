# flūmine

[![Build Status](https://travis-ci.org/liampauling/flumine.svg?branch=master)](https://travis-ci.org/liampauling/flumine) [![Coverage Status](https://coveralls.io/repos/github/liampauling/flumine/badge.svg?branch=master)](https://coveralls.io/github/liampauling/flumine?branch=master) [![PyPI version](https://badge.fury.io/py/flumine.svg)](https://pypi.python.org/pypi/flumine)


Betfair trading framework with a focus on:

- simplicity
- modular
- pythonic
- rock-solid
- safe

Support for market and custom streaming data (order, score and custom polling data in development)

[docs](https://liampauling.github.io/flumine/)

[join slack group](https://betfairlightweight.herokuapp.com)

Currently tested on Python 3.5, 3.6, 3.7 and 3.8.

## installation

```
$ pip install flumine
```

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
from betfairlightweight.filters import streaming_market_filter


class ExampleStrategy(BaseStrategy):
    def start(self):
        # subscribe to streams
        print("starting strategy 'ExampleStrategy'")

    def check_market_book(self, market, market_book):
        # process_market_book only executed if this returns True
        if market_book.status != "CLOSED":
            return True

    def process_market_book(self, market, market_book):
        # process marketBook object
        print(market_book.status)


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
- Order execution (in development)
- Paper trading (in development)
- Back testing (in development)
- Analytics (in development)
- Scores / RaceCard / InPlayService (in development)

## Dependencies

flumine relies on these libraries:

* `betfairlightweight` - Betfair API support.
* `tenacity` - Used for connection retrying (streaming).
* `python-json-logger` - JSON logging.
