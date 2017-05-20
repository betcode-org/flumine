# flumine

[![Build Status](https://travis-ci.org/liampauling/flumine.svg?branch=master)](https://travis-ci.org/liampauling/flumine) [![Coverage Status](https://coveralls.io/repos/github/liampauling/flumine/badge.svg?branch=master)](https://coveralls.io/github/liampauling/flumine?branch=master)


Betfair data record framework utilising streaming, requires [betfairlightweight](https://github.com/liampauling/betfairlightweight).

IN DEVELOPMENT.

# installation

```
$ pip install flumine
```

# setup

The framework can be used as follows:

```python
>>> import flumine

>>> flumine = flumine.Flumine(
            trading=('username', 'password'),
            recorder=flumine.DataRecorder(in_play=False)
    )
>>> flumine.start()

>>> flumine
<Flumine [running]>

>>> flumine.stop()

>>> flumine
<Flumine [not running]>

```
