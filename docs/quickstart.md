# QuickStart

## Live

!!! tip
    flumine uses `betfairlightweight` for communicating with the Betfair API, please see [docs](https://betcode-org.github.io/betfair/) for how to use/setup before proceeding.

First, start by importing flumine/bflw and creating a trading and framework client:

```python
import betfairlightweight
from flumine import Flumine, clients

trading = betfairlightweight.APIClient("username")
client = clients.BetfairClient(trading)

framework = Flumine(client=client)
```

!!! note
    flumine will handle login, logout and keep alive whilst the framework is running using the `keep_alive` worker.

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

### Order placement

Orders can be placed as followed:

```python
from flumine.order.trade import Trade
from flumine.order.order import LimitOrder


class ExampleStrategy(BaseStrategy):
    def process_market_book(self, market, market_book):
        for runner in market_book.runners:
            if runner.selection_id == 123:
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
```

This order will be validated through controls, stored in the blotter and sent straight to the execution thread pool for execution. It is also possible to batch orders into transactions as follows:

```python
with market.transaction() as t:
    market.place_order(order)  # executed immediately in separate transaction
    t.place_order(order)  # executed on transaction __exit__

with market.transaction() as t:
    t.place_order(order)
    
    t.execute()  # above order executed
    
    t.cancel_order(order)
    t.place_order(order)  # both executed on transaction __exit__
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

The OrderDataStream class can be used to record order data as per market:

```python
from flumine.streams.datastream import OrderDataStream

strategy = ExampleDataStrategy(
    market_filter=None,
    stream_class=OrderDataStream
)

flumine.add_strategy(strategy)
```

## Paper Trading

Flumine can be used to paper trade strategies live using the following code:

```python
from flumine import clients

client = clients.BetfairClient(trading, paper_trade=True)
```

Market data will be recieved as per live but any orders will use Simulated execution and Simulated order polling to replicate live trading.

!!! tip
    This can be handy when testing strategies as the betfair website can be used to validate the market.

## Simulation

Flumine can be used to simulate strategies using the following code:

```python
from flumine import FlumineSimulation, clients

client = clients.SimulatedClient()
framework = FlumineSimulation(client=client)

strategy = ExampleStrategy(
    market_filter={"markets": ["/tmp/marketdata/1.170212754"]}
)
framework.add_strategy(strategy)

framework.run()
```

Note the use of market filter to pass the file directories.

### Listener kwargs

Sometimes a subset of the market lifetime is required, this can be optimised by limiting the number of updates to process resulting in faster simulation:

```python
strategy = ExampleStrategy(
    market_filter={
        "markets": ["/tmp/marketdata/1.170212754"],
        "listener_kwargs": {"inplay": False, "seconds_to_start": 600},
    }
)
```

- inplay: Filter inplay flag
- seconds_to_start: Filter market seconds to start
- calculate_market_tv: As per bflw listener arg
- cumulative_runner_tv: As per bflw listener arg

The extra kwargs above will limit processing to preplay in the final 10 minutes.

!!! tip
    Multiple strategies and markets can be passed, flumine will pass the MarketBooks to the correct strategy via its subscription.

### Event Processing

It is also possible to process events with multiple markets such as win/place in racing or all football markets as per live by adding the following flag:

```python
strategy = ExampleStrategy(
    market_filter={"markets": [..], "event_processing": True}
)
```

To process multiple events in parallel, provide a mapping for event groups in the format `{event_id: event_group}`. In this example, events with IDs `"123"` and `"456"` are added to execution group `"A"` and will be simulated together.
```python
strategy = ExampleStrategy(
    market_filter={"markets": [..], "event_processing": True, "event_groups": {"123": "A", "456": "A"}}
)
```

The `Market` object contains a helper method for accessing other event linked markets:

```python
place_market = market.event["PLACE"]
```

### Market Filter

When simulating you can filter markets to be processed by using the `market_type` and `country_code` filter as per live:

```python
strategy = ExampleStrategy(
    market_filter={"markets": [..], "market_types": ["MATCH_ODDS"], "country_codes": ["GB"]}
)
```

### Simulation

Simulation uses the `SimulatedExecution` execution class and tries to accurately simulate matching with the following:

- Place/Cancel/Replace latency delay added
- BetDelay added based on market state
- Queue positioning based on liquidity available
- Order lapse on market version change
- Order lapse and reduction on runner removal
- BSP

Limitations #192:

- Queue cancellations
- Double counting of liquidity (active)
- Currency fluctuations
