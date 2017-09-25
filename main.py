import sys
import json
import logging

from flumine.resources import StreamRecorder
from flumine.storage import storageengine
from flumine import (
    Flumine,
    FlumineException,
)


def setup_logging():
    logger = logging.getLogger('betfairlightweight')
    logger.setLevel(logging.INFO)
    logging.basicConfig(
        format='%(asctime)s | %(levelname)s | %(message)s | %(filename)s | %(module)s',
        level=logging.INFO
    )


def main():
    setup_logging()

    logging.info(sys.argv)

    try:
        market_filter = json.loads(sys.argv[1])
    except IndexError:
        logging.warning('Market Filter not provided, defaulting to GB racing')
        market_filter = {"eventTypeIds": ["7"], "countryCodes": ["GB", "IE"], "marketTypes": ["WIN"]}
    except json.JSONDecodeError:
        logging.error('Market Filter arg must be provided in json format')
        raise

    try:
        market_data_filter = json.loads(sys.argv[2])
    except IndexError:
        logging.warning('Market Data Filter not provided, defaulting to None')
        market_data_filter = None
    except json.JSONDecodeError:
        logging.error('Market Data Filter arg must be provided in json format')
        market_data_filter = None

    storage_engine = storageengine.S3('flumine')
    # storage_engine = storageengine.Local('/fluminetests')

    flumine = Flumine(
        recorder=StreamRecorder(
            storage_engine=storage_engine,
            market_filter=market_filter,
            market_data_filter=market_data_filter,
        ),
    )

    try:
        flumine.start(async=False)
    except FlumineException:
        pass


if __name__ == '__main__':
    main()
