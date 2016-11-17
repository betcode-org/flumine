# flumine

[![Build Status](https://travis-ci.org/liampauling/flumine.svg?branch=master)](https://travis-ci.org/liampauling/flumine) [![Coverage Status](https://coveralls.io/repos/github/liampauling/flumine/badge.svg?branch=master)](https://coveralls.io/github/liampauling/flumine?branch=master)


Betfair data record framework utilising streaming, requires [betfairlightweight](https://github.com/liampauling/betfairlightweight).

IN DEVELOPMENT.

# setup

The framework can be used as follows:

```python
>>> import betfairlightweight
>>> from flumine import Flumine

>>> trading = betfairlightweight.APIClient('username', 'password', app_key='app_key')

>>> market_filter = {
        'eventTypeIds': ['7'],
        'countryCodes': ['GB'],
        'marketTypes': ['WIN']
    }
>>> market_data_filter = {
        'fields': ['EX_BEST_OFFERS', 'EX_MARKET_DEF'],
        'ladderLevels': 1
    }

>>> flumine = Flumine(trading, [])
>>> flumine.start(
        market_filter=market_filter,
        market_data_filter=market_data_filter
    )
```
