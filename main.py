import logging
import betfairlightweight

from flumine.resources import MarketRecorder
from flumine.storage import storageengine
from flumine import Flumine, FlumineException, __version__


def setup_logging():
    logger = logging.getLogger("betfairlightweight")
    logger.setLevel(logging.INFO)
    logging.basicConfig(
        format="%(asctime)s | %(levelname)s | %(message)s | %(filename)s | %(module)s",
        level=logging.INFO,
    )


def main(s3_bucket, market_filter=None, market_data_filter=None, settings=None):
    setup_logging()
    logging.info("betfairlightweight version: %s" % betfairlightweight.__version__)
    logging.info("flumine version: %s" % __version__)

    logging.info('Creating "storageengine.s3"')
    storage_engine = storageengine.S3(s3_bucket)

    logging.info('Creating "MarketRecorder"')
    recorder = MarketRecorder(
        storage_engine=storage_engine,
        market_filter=market_filter,
        market_data_filter=market_data_filter,
    )

    flumine = Flumine(recorder=recorder, settings=settings)
    try:
        flumine.start(async_=False)
    except FlumineException as e:
        logging.critical("Major flumine error: %s" % e)


if __name__ == "__main__":
    main(
        s3_bucket="flumine",  # need to create in aws
        market_filter={  # (optional)
            "eventTypeIds": ["7"],
            "countryCodes": ["GB", "IE"],
            "marketTypes": ["WIN"],
        },
        market_data_filter={  # (optional)
            "ladderLevels": 1,
            "fields": [
                "EX_BEST_OFFERS",
                "SP_TRADED",
                "SP_PROJECTED",
                "EX_TRADED_VOL",
                "EX_LTP",
                "EX_MARKET_DEF",
            ],
        },
        settings={
            "betfairlightweight": {"username": "johnsmith"},
            "certificate_login": False,
        },  # bflw settings (username/password etc.)
    )
