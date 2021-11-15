import os
import json
import time
import logging
import gzip
import boto3
import queue
import threading
from boto3.s3.transfer import S3Transfer, TransferConfig
from botocore.exceptions import BotoCoreError

from flumine import BaseStrategy
from flumine.utils import create_short_uuid, file_line_count

logger = logging.getLogger(__name__)


class MarketRecorder(BaseStrategy):

    """
    Simple raw streaming market recorder, context:

        market_expiration: int, Seconds to wait after market closure before removing files
        remove_file: bool, Remove txt file during cleanup
        remove_gz_file: bool, Remove gz file during cleanup
        force_update: bool, Update zip/closure if update received after closure
        load_market_catalogue: bool, Store marketCatalogue as {marketId}.json
        local_dir: str, Dir to store data
        recorder_id: str, Directory name (defaults to random uuid)
    """

    MARKET_ID_LOOKUP = "id"

    def __init__(self, *args, **kwargs):
        BaseStrategy.__init__(self, *args, **kwargs)
        self._market_expiration = self.context.get("market_expiration", 3600)  # seconds
        self._remove_file = self.context.get("remove_file", False)
        self._remove_gz_file = self.context.get("remove_gz_file", False)
        self._force_update = self.context.get("force_update", True)
        self._load_market_catalogue = self.context.get("load_market_catalogue", True)
        self.local_dir = self.context.get("local_dir", "/tmp")
        self.recorder_id = self.context.get("recorder_id", create_short_uuid())
        self._loaded_markets = []  # list of marketIds
        self._queue = queue.Queue()

    def add(self) -> None:
        logger.info("Adding strategy %s with id %s" % (self.name, self.recorder_id))
        # check local dir
        if not os.path.isdir(self.local_dir):
            raise OSError("File dir %s does not exist" % self.local_dir)
        # create sub dir
        directory = os.path.join(self.local_dir, self.recorder_id)
        if not os.path.exists(directory):
            os.makedirs(directory)

    def start(self) -> None:
        # start load processor thread
        threading.Thread(
            name="{0}_load_processor".format(self.name),
            target=self._load_processor,
            daemon=True,
        ).start()

    def process_raw_data(self, clk: str, publish_time: int, data: dict):
        market_id = data.get(self.MARKET_ID_LOOKUP)
        file_directory = os.path.join(self.local_dir, self.recorder_id, market_id)
        with open(file_directory, "a") as f:
            f.write(
                json.dumps(
                    {"op": "mcm", "clk": clk, "pt": publish_time, "mc": [data]},
                    separators=(",", ":"),
                )
                + "\n"
            )

    def process_closed_market(self, market, data: dict) -> None:
        market_id = data.get(self.MARKET_ID_LOOKUP)
        if market_id in self._loaded_markets:
            if self._force_update:
                logger.warning(
                    "File: /{0}/{1}/{2} has already been loaded, updating..".format(
                        self.local_dir, self.recorder_id, market_id
                    )
                )
            else:
                return
        else:
            self._loaded_markets.append(market_id)
        logger.info("Closing market %s" % market_id)

        file_dir = os.path.join(self.local_dir, self.recorder_id, market_id)
        market_definition = data.get("marketDefinition")

        # check that file actually exists
        if not os.path.isfile(file_dir):
            logger.error(
                "File: %s does not exist in /%s/%s/"
                % (self.local_dir, market_id, self.recorder_id)
            )
            return

        # check that file is not empty / 1 line (i.e. the market had already closed on startup)
        line_count = file_line_count(file_dir)
        if line_count == 1:
            logger.warning(
                "File: %s contains one line only and will not be loaded (already closed on startup)"
                % file_dir
            )
            return

        self._queue.put((market, file_dir, market_definition))

    def _load_processor(self):
        # process compression/load in thread
        while True:
            market, file_dir, market_definition = self._queue.get(block=True)
            # check file still exists (potential race condition)
            if not os.path.isfile(file_dir):
                logger.warning(
                    "File: %s does not exist in %s" % (market.market_id, file_dir)
                )
                continue
            # compress file
            compress_file_dir = self._compress_file(file_dir)
            # core load code
            self._load(market, compress_file_dir, market_definition)
            # clean up
            self._clean_up()

    def _compress_file(self, file_dir: str) -> str:
        """compresses txt file into filename.gz"""
        compressed_file_dir = "{0}.gz".format(file_dir)
        with open(file_dir, "rb") as f:
            with gzip.open(compressed_file_dir, "wb") as compressed_file:
                compressed_file.writelines(f)
        return compressed_file_dir

    def _load(self, market, compress_file_dir: str, market_definition: dict) -> None:
        # store marketCatalogue data `{marketId}.json.gz`
        if market and self._load_market_catalogue:
            if market.market_catalogue is None:
                logger.warning(
                    "No marketCatalogue data available for %s" % market.market_id
                )
                return
            market_catalogue_compressed = self._compress_catalogue(
                market.market_catalogue
            )
            # save to file
            file_dir = os.path.join(
                self.local_dir, self.recorder_id, "{0}.json.gz".format(market.market_id)
            )
            with open(file_dir, "wb") as f:
                f.write(market_catalogue_compressed)

    @staticmethod
    def _compress_catalogue(market_catalogue) -> bytes:
        market_catalogue_dumped = market_catalogue.json()
        if isinstance(market_catalogue_dumped, str):
            market_catalogue_dumped = market_catalogue_dumped.encode("utf-8")
        return gzip.compress(market_catalogue_dumped)

    def _clean_up(self) -> None:
        """If gz > market_expiration old remove
        gz and txt file
        """
        directory = os.path.join(self.local_dir, self.recorder_id)
        for file in os.listdir(directory):
            if file.endswith(".gz"):
                gz_path = os.path.join(directory, file)
                file_stats = os.stat(gz_path)
                seconds_since = time.time() - file_stats.st_mtime
                if seconds_since > self._market_expiration:
                    if self._remove_gz_file:
                        logger.info(
                            "Removing: %s, age: %ss"
                            % (gz_path, round(seconds_since, 2))
                        )
                        os.remove(gz_path)
                    txt_path = os.path.join(directory, file.split(".gz")[0])
                    if os.path.exists(txt_path) and self._remove_file:
                        file_stats = os.stat(txt_path)
                        seconds_since = time.time() - file_stats.st_mtime
                        if seconds_since > self._market_expiration:
                            logger.info(
                                "Removing: %s, age: %ss"
                                % (txt_path, round(seconds_since, 2))
                            )
                            os.remove(txt_path)

    @staticmethod
    def _create_metadata(market_definition: dict) -> dict:
        try:
            del market_definition["runners"]
        except KeyError:
            pass
        return dict([a, str(x)] for a, x in market_definition.items())


class S3MarketRecorder(MarketRecorder):
    """
    AWS S3 version of the market recorder
    to automate loading of compressed file
    and marketCatalogue on closure.

        bucket: str, bucket name
        data_type: str, data type
    """

    def __init__(self, *args, **kwargs):
        MarketRecorder.__init__(self, *args, **kwargs)
        self._bucket = self.context["bucket"]
        self._data_type = self.context.get("data_type", "marketdata")
        self._default_event_type_id = self.context.get("default_event_type_id", "7")
        self.s3 = boto3.client("s3")
        transfer_config = TransferConfig(use_threads=False)
        self.transfer = S3Transfer(self.s3, config=transfer_config)

    def add(self) -> None:
        super().add()
        self.s3.head_bucket(Bucket=self._bucket)  # validate bucket/access

    def _load(self, market, compress_file_dir: str, market_definition: dict) -> None:
        # load to s3
        event_type_id = (
            market_definition.get("eventTypeId", 0) if market_definition else self._default_event_type_id
        )
        try:
            self.transfer.upload_file(
                filename=compress_file_dir,
                bucket=self._bucket,
                key=os.path.join(
                    self._data_type,
                    "streaming",
                    event_type_id,
                    os.path.basename(compress_file_dir),
                ),
                extra_args={
                    "Metadata": self._create_metadata(market_definition)
                    if market_definition
                    else {}
                },
            )
            logger.info("%s successfully loaded to s3" % compress_file_dir)
        except (BotoCoreError, Exception) as e:
            logger.error("Error loading to s3: %s" % e)

        # upload marketCatalogue data
        if market and self._load_market_catalogue:
            if market.market_catalogue is None:
                logger.warning(
                    "No marketCatalogue data available for %s" % market.market_id
                )
                return
            market_catalogue_compressed = self._compress_catalogue(
                market.market_catalogue
            )
            try:
                self.s3.put_object(
                    Body=market_catalogue_compressed,
                    Bucket=self._bucket,
                    Key=os.path.join(
                        self._data_type,
                        "marketCatalogue",
                        "{0}.gz".format(market.market_id),
                    ),
                )
                logger.info(
                    "%s successfully loaded marketCatalogue to s3" % market.market_id
                )
            except (BotoCoreError, Exception) as e:
                logger.error("Error loading to s3: %s" % e)
