import sys
import json
import logging
import betfairlightweight

from flumine.resources import MarketRecorder, RaceRecorder
from flumine.storage import storageengine
from flumine import Flumine, FlumineException, __version__


def setup_logging():
    logger = logging.getLogger("betfairlightweight")
    logger.setLevel(logging.INFO)
    logging.basicConfig(
        format="%(asctime)s | %(levelname)s | %(message)s | %(filename)s | %(module)s",
        level=logging.INFO,
    )


def main():
    setup_logging()
    logging.info(sys.argv)

    try:
        s3_bucket = sys.argv[1]
    except IndexError:
        logging.error("s3 bucket not provided")
        raise

    try:
        stream_type = sys.argv[2]
    except IndexError:
        stream_type = "market"

    logging.info("betfairlightweight version: %s" % betfairlightweight.__version__)
    logging.info("flumine version: %s" % __version__)

    if stream_type == "race":
        logging.info('Creating "storageengine.s3"')
        storage_engine = storageengine.S3(
            s3_bucket, data_type="racedata", force_update=False
        )
        logging.info('Creating "RaceRecorder"')
        recorder = RaceRecorder(storage_engine=storage_engine)
    elif stream_type == "market":
        try:
            market_filter = json.loads(sys.argv[3])
        except IndexError:
            logging.warning(
                "Market Filter not provided, defaulting to GB and IE WIN racing"
            )
            market_filter = {
                "eventTypeIds": ["7"],
                "countryCodes": ["GB", "IE"],
                "marketTypes": ["WIN"],
            }
        except json.JSONDecodeError:
            logging.error("Market Filter arg must be provided in json format")
            raise

        try:
            market_data_filter = json.loads(sys.argv[4])
        except IndexError:
            logging.warning("Market Data Filter not provided, defaulting to None")
            market_data_filter = None
        except json.JSONDecodeError:
            logging.error("Market Data Filter arg must be provided in json format")
            market_data_filter = None

        logging.info('Creating "storageengine.s3"')
        storage_engine = storageengine.S3(s3_bucket, data_type="marketdata")
        logging.info('Creating "MarketRecorder"')
        recorder = MarketRecorder(
            storage_engine=storage_engine,
            market_filter=market_filter,
            market_data_filter=market_data_filter,
        )
    else:
        raise ValueError('Invalid stream_type must be "race" or "market"')

    flumine = Flumine(recorder=recorder, settings={"certificate_login": False})
    try:
        flumine.start(async_=False)
    except FlumineException as e:
        logging.critical("Major flumine error: %s" % e)


if __name__ == "__main__":
    """
    sys.argv[1] == s3 bucket
    sys.argv[2] == race or market
    if market:
        sys.argv[3] == market_filter (optional)
        sys.argv[4] == market_data_filter (optional)
    """
    main()
