import logging

from flumine.resources import StreamRecorder
from flumine.storage import storageengine
from flumine import (
    Flumine,
    FlumineException,
)


def setup_logging():
    logger = logging.getLogger('betfairlightweight')
    logger.setLevel(logging.DEBUG)

    custom_format = '%(asctime) %(levelname) %(message) %(filename) %(funcName) %(module) %(process) %(threadName)'
    log_handler = logging.StreamHandler()

    logger = logging.getLogger()
    # formatter = jsonlogger.JsonFormatter(custom_format)
    # formatter.converter = time.gmtime
    # log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)
    logger.setLevel(logging.INFO)


def main():
    market_filter = {"marketIds": ["1.132452335"]}
    market_data_filter = None
    storage_engine = storageengine.S3('flumine')

    flumine = Flumine(
        settings={'betfairlightweight': {'username': 'LiamPauling'}},
        recorder=StreamRecorder(
            storage_engine=storage_engine,
            market_filter=market_filter,
            market_data_filter=market_data_filter,
        ),
    )

    try:
        flumine.start()
    except FlumineException:
        pass

    import time
    while True:
        time.sleep(1)

if __name__ == '__main__':
    main()
