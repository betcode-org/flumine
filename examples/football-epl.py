import logging

from flumine.resources import StreamRecorder
from flumine.storage import storageengine
from flumine import (
    Flumine,
    FlumineException,
)


# EPL competition id = 10932509


class EPLRecorder(StreamRecorder):

    def check_market_book(self, market_id, market_book):
        # check if market is EPL..

        if market_id not in self.live_markets:
            self.live_markets.append(market_id)


def setup_logging():
    logger = logging.getLogger('betfairlightweight')
    logger.setLevel(logging.INFO)
    logging.basicConfig(
        format='%(asctime)s | %(levelname)s | %(message)s | %(filename)s | %(module)s',
        level=logging.INFO
    )


def main():
    setup_logging()

    market_filter = {
        "eventTypeIds": ["1"],
        "countryCodes": ["GB"],
        "marketTypes": ["MATCH_ODDS", "OVER_UNDER_25", "CORRECT_SCORE"]
    }

    storage_engine = storageengine.S3('flumine')

    flumine = Flumine(
        recorder=EPLRecorder(
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
