# flumine

[![Build Status](https://travis-ci.org/liampauling/flumine.svg?branch=master)](https://travis-ci.org/liampauling/flumine) [![Coverage Status](https://coveralls.io/repos/github/liampauling/flumine/badge.svg?branch=master)](https://coveralls.io/github/liampauling/flumine?branch=master) [![PyPI version](https://badge.fury.io/py/flumine.svg)](https://pypi.python.org/pypi/flumine)


Betfair data record framework utilising streaming and flask to create a simple rest API, requires [betfairlightweight](https://github.com/liampauling/betfairlightweight).

IN DEVELOPMENT.

## roadmap

- fully functional rest api
- interactive frontend (similiar to portainer.io)
- storage engine (s3 / google cloud etc.)
- logging control class
- docker
- cli (e.g. flumine create app, creates run.py and flumine_settings.json)

## setup

The framework can be used as follows:

- clone library
- navigate to flumine
- update flumine_settings.json with username/password etc.

```bash
$ python run.py
```

## settings
```javascript
{
    "betfairlightweight": {  // passed to APIClient
        "username": "username",  // required
        "password": null,
        "app_key": null,
        "certs": null,
        "locale": null,
        "cert_files": null
    },
    "streaming": {  // default settings
        "heartbeat_ms": null,
        "conflate_ms": null,
        "segmentation_enabled": true
    },
    "storage": {  // storage engine used to store recorded data
        "engine": "S3",  // engine type, can be S3 or LOCAL
        "settings": {
            "directory": "flumine-test",  // bucket name in this case
            "access_key": null,  // optional
            "secret_key": null  // optional
        }
    }
}
```

## use

### Top level:
```bash
$ curl http://localhost:8080/api -H "Content-Type: application/json"
{
  "recorders": "/api/recorder",
  "settings": "/api/settings",
  "storage": "/api/storage",
  "streams": "/api/stream"
}
```

### View settings:
```bash
$ curl http://localhost:8080/api/settings -H "Content-Type: application/json"
{
    "betfairlightweight": {
        "username": "username",
        "password": null,
        "app_key": null,
        "certs": null,
        "locale": null,
        "cert_files": null
    },
    "streaming": {
        "heartbeat_ms": null,
        "conflate_ms": null,
        "segmentation_enabled": true
    },
    "storage": {
        "engine": "S3",
        "settings": {
            "directory": "flumine-test",
            "access_key": null,
            "secret_key": null
        }
    }
}
```

### View recorders:
```bash
$ curl http://localhost:8080/api/recorder -H "Content-Type: application/json"
{
    "BASE_RECORDER": {
        "name": "BaseRecorder"
    },
    "DATA_RECORDER": {
        "name": "DataRecorder"
    },
    "STREAM_RECORDER": {
        "name": "StreamRecorder"
    }
}
```

### View storage engine:
```bash
$ curl http://localhost:8080/api/storage -H "Content-Type: application/json"
{
  "directory": "flumine-test",
  "markets_loaded": [],
  "markets_loaded_count": 0,
  "name": "S3"
}
```

### Create stream:
```bash
$ curl http://localhost:8080/api/stream -d '{"market_filter": {"eventTypeIds":["7"], "countryCodes":["IE"], "market_types":["WIN"]}, "recorder": "STREAM_RECORDER"}' -X POST -v -H "Content-Type: application/json"
{
    "description": null,
    "market_data_filter": null,
    "market_filter": {
        "countryCodes": [
            "IE"
        ],
        "eventTypeIds": [
            "7"
        ],
        "market_types": [
            "WIN"
        ]
    },
    "recorder": "STREAM_RECORDER",
    "running": false,
    "unique_id": 1000
}
```

### View all streams:
```bash
$ curl http://localhost:8080/api/stream -H "Content-Type: application/json"
{
    "aea9ee72": {
        "description": null,
        "market_data_filter": null,
        "market_filter": {
            "countryCodes": [
                "IE"
            ],
            "eventTypeIds": [
                "7"
            ],
            "market_types": [
                "WIN"
            ]
        },
        "recorder": "BASE_RECORDER",
        "running": false,
        "unique_id": 1000
    }
}
```

### View stream detail:
```bash
$ curl http://localhost:8080/api/stream/aea9ee72 -H "Content-Type: application/json"
{
    "description": null,
    "listener": {
        "market_count": null,
        "stream_type": null,
        "time_created": null,
        "time_updated": null,
        "updates_processed": null
    },
    "market_data_filter": null,
    "market_filter": {
        "countryCodes": [
            "IE"
        ],
        "eventTypeIds": [
            "7"
        ],
        "market_types": [
            "WIN"
        ]
    },
    "recorder": "BASE_RECORDER",
    "running": false,
    "status": "not running",
    "unique_id": 1000
}
```

### Start/stop stream:
```bash
$ curl http://localhost:8080/api/stream/aea9ee72/start?conflate_ms=2000 -H "Content-Type: application/json"
{
    "error": null,
    "error_code": null,
    "success": true
}
```
