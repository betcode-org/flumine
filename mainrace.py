import sys
import logging

from flumine.resources import RaceRecorder
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

    # storage_engine = storageengine.S3('flumine')
    storage_engine = storageengine.Local('/tmp')

    flumine = Flumine(
        recorder=RaceRecorder(
            storage_engine=storage_engine,
        ),
    )

    try:
        flumine.start(async=False)
    except FlumineException:
        pass


if __name__ == '__main__':
    main()
