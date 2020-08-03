# QuickStart

## Live

!!! tip
    flumine uses `betfairlightweight` for communicating with the Betfair API, please see [docs](https://liampauling.github.io/betfair/) for how to use/setup before proceeding.

First, start by importing flumine/bflw and creating a trading and framework client:

```python
import betfairlightweight
from flumine import Flumine, clients

trading = betfairlightweight.APIClient("username")
client = clients.BetfairClient(trading)

framework = Flumine(client=client)
```

!!! note
    flumine will handle login, logout and keep alive whilst the framework is running.

A strategy can now be created by using the BaseStrategy class:

```python
from flumine import BaseStrategy


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
```

This strategy can now be initiated with the market and data filter before being added to the framework:

```python
from betfairlightweight.filters import (
    streaming_market_filter, 
    streaming_market_data_filter,
)

strategy = ExampleStrategy(
    market_filter=streaming_market_filter(
        event_type_ids=["7"],
        country_codes=["GB"],
        market_types=["WIN"],
    ),
    market_data_filter=streaming_market_data_filter(fields=["EX_ALL_OFFERS"])
)

framework.add_strategy(strategy)
```

The framework can now be started:

```python
framework.run()
```

### Stream class

By default the stream class will be a MarketStream which provides a MarketBook python object, if collecting data this can be changed to a DataStream class however process_raw_data will be called and not process_market_book:


```python
from flumine import BaseStrategy
from flumine.streams.datastream import DataStream


class ExampleDataStrategy(BaseStrategy):
    def process_raw_data(self, publish_time, data):
        print(publish_time, data)
        
strategy = ExampleDataStrategy(
    market_filter=streaming_market_filter(
        event_type_ids=["7"],
        country_codes=["GB"],
        market_types=["WIN"],
    ),
    stream_class=DataStream
)

flumine.add_strategy(strategy)
```

## Paper Trading

Flumine can be used to paper trade strategies live using the following code:

```python
import betfairlightweight
from flumine import Flumine, clients

trading = betfairlightweight.APIClient("username")
client = clients.BetfairClient(trading, paper_trade=True)
framework = Flumine(client=client)

strategy = ExampleStrategy(
    market_filter={"markets": ["/tmp/marketdata/1.170212754"]}
)
framework.add_strategy(strategy)

framework.run()
```

Market data will be recieved as per live but any orders will use Simulated execution and Simulated order polling to replicate live trading.

!!! tip
    This can be handy when testing strategies as the betfair website can be used to validate the market.

## Backtesting

Flumine can be used to backtest strategies using the following code:

```python
from flumine import FlumineBacktest, clients

client = clients.BacktestClient()
framework = FlumineBacktest(client=client)

strategy = ExampleStrategy(
    market_filter={"markets": ["/tmp/marketdata/1.170212754"]}
)
framework.add_strategy(strategy)

framework.run()
```

Note the use of market filter to pass the file directories.

!!! tip
    Multiple strategies and markets can be passed, flumine will pass the MarketBooks to the correct strategy via its subscription.
