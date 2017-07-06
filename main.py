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

    try:
        market_filter = json.loads(sys.argv[1])
    except (json.JSONDecodeError, IndexError):
        logging.error('Market Filter arg must be provided in json format')
        raise
    storage_engine = storageengine.S3('flumine')

    flumine = Flumine(
        recorder=StreamRecorder(
            storage_engine=storage_engine,
            market_filter=market_filter,
        ),
    )

    try:
        flumine.start(async=False)
    except FlumineException:
        pass

if __name__ == '__main__':
    main()
