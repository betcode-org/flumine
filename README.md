# flūmine

[![Build Status](https://travis-ci.org/liampauling/flumine.svg?branch=master)](https://travis-ci.org/liampauling/flumine) [![Coverage Status](https://coveralls.io/repos/github/liampauling/flumine/badge.svg?branch=master)](https://coveralls.io/github/liampauling/flumine?branch=master) [![PyPI version](https://badge.fury.io/py/flumine.svg)](https://pypi.python.org/pypi/flumine)


Betfair data record framework utilising streaming to create a simple data recorder, requires [betfairlightweight](https://github.com/liampauling/betfairlightweight).

Currently tested on Python 3.5, 3.6, 3.7 and 3.8.

## roadmap

- storage engine (s3 / google cloud etc.)
- logging control class
- cli (e.g. flumine start / stop)

## installation

```
$ pip install flumine
```

## setup

The framework can be used as follows:

```python
from flumine import Flumine
from flumine.resources import MarketRecorder
from flumine.storage import storageengine

market_filter = {"marketIds": ["1.132452335"]}

storage_engine = storageengine.Local(directory="/tmp")

flumine = Flumine(
    recorder=MarketRecorder(
        storage_engine=storage_engine,
        market_filter=market_filter,
    ),
    settings={  # passed to betfairlightweight
        "betfairlightweight": {
            "username": "test",
            "password": "test",
            "app_key": "test",
        },
        "certificate_login": False,
    }
)

flumine.start(async_=True)

print(flumine)
# <Flumine [running]>

flumine.stop()

print(flumine)
# <Flumine [not running]>
```

See main.py for example.
