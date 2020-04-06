<h1 align="center" style="font-size: 3rem; margin: -15px 0">
flūmine
</h1>

---

<div align="center">
<p>
<a href="https://travis-ci.org/liampauling/flumine">
    <img src="https://travis-ci.org/liampauling/flumine.svg?branch=master" alt="Build Status">
</a>
<a href="https://coveralls.io/github/liampauling/flumine?branch=master">
    <img src="https://coveralls.io/repos/github/liampauling/flumine/badge.svg?branch=master" alt="Coverage">
</a>
<a href="https://pypi.python.org/pypi/flumine">
    <img src="https://badge.fury.io/py/flumine.svg" alt="Package version">
</a>
</p>
</div>

Betfair trading framework with a focus on:

- simplicity
- modular
- pythonic
- rock-solid
- safe

Support for market and custom streaming data (order, score and custom polling data in development)

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
        
    def check_market_book(self, market_book):
        # process_market_book only executed if this returns True
        if market_book.status != "CLOSED":
            return True

    def process_market_book(self, market_book):
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

!!! danger
    By default flumine will try and prevent coding errors which result in [flash crashes](https://en.wikipedia.org/wiki/Flash_crash) and [burnt fingers](https://www.betangel.com/forum/viewtopic.php?f=5&t=2458) but use at your own risk as per the MIT license.
    
    Recommendation is not to remove the [trading controls](/advanced) and carry out extensive testing before executing on live markets, even then only use new strategies on an account with a small balance (transfer balance to games wallet).

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

## Installation

Install with pip:

```shell
$ pip install flumine
```

flumine requires Python 3.5+
