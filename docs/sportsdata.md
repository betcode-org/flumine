# Sports Data

Flumine is able to connect to the sports-data-stream provided by Betfair for live data on cricket and races.

!!! tip
    Your appKey must be authorised to access the sports-data stream, contact bdp@betfair.com

## Cricket Subscription

A cricket subscription can be added via the `SportsDataStream`

```python 
sports_data_stream = SportsDataStream(
    sports_data_filter="cricketSubscription",
)
framework.add_stream(sports_data_stream)
```

## Race Subscription

A race subscription can be added via the `SportsDataStream`

```python 
sports_data_stream = SportsDataStream(
    sports_data_filter="raceSubscription",
)
framework.add_stream(sports_data_stream)
```

## Strategy

Once subscribed any sports data stream updates will be available in the strategy via the `process_sports_data` function

```python
class ExampleStrategy(BaseStrategy):
    def process_sports_data(
        self, market: Market, sports_data: Union[Race, CricketMatch]
    ) -> None:
        # called on each update from sports-data-stream
        print(market, sports_data)
```


## Data Recorder

The example `marketrecorder.py` can be modified to record race and cricket data by updating the `process_raw_data` with the matching `op` and data keys.

- marketSubscription `mcm` and `mc`
- orderSubscription `ocm` and `oc`
- cricketSubscription `ccm` and `cc`
- raceSubscription `rcm` and `rc`

And using the correct stream class:

#### Cricket Recorder
```python
from flumine.streams.betfairdatastream import BetfairCricketDataStream

strategy= MarketRecorder(
    stream=BetfairCricketDataStream(framework),
    context={
        "local_dir": "/tmp",
        "force_update": False,
        "remove_file": True,
        "remove_gz_file": False,
    },
)
```

#### Race Recorder
```python
from flumine.streams.betfairdatastream import BetfairRaceDataStream

strategy= MarketRecorder(
    stream=BetfairRaceDataStream(framework),
    context={
        "local_dir": "/tmp",
        "force_update": False,
        "remove_file": True,
        "remove_gz_file": False,
    },
)
```
