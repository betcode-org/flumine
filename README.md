# flumine

[![Build Status](https://travis-ci.org/liampauling/flumine.svg?branch=master)](https://travis-ci.org/liampauling/flumine) [![Coverage Status](https://coveralls.io/repos/github/liampauling/flumine/badge.svg?branch=master)](https://coveralls.io/github/liampauling/flumine?branch=master)


Betfair data record framework utilising streaming, requires [betfairlightweight](https://github.com/liampauling/betfairlightweight).

IN DEVELOPMENT.

# setup

The framework can be used as follows:

```python
>>> import flumine
>>> import betfairlightweight

>>> trading = betfairlightweight.APIClient('username', 'password', app_key='app_key')

>>> flumine = flumine.Flumine(
            trading=trading,
            recorder=flumine.RacingRecorder(in_play=False)
    )
>>> flumine.start()

>>> flumine
<Flumine [running]>

>>> flumine.stop()

>>> flumine
<Flumine [not running]>

```
