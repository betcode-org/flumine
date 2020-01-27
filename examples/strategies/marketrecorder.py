import os
import json
import logging
import zipfile

from flumine import BaseStrategy
from flumine.utils import create_short_uuid

logger = logging.getLogger(__name__)


class MarketRecorder(BaseStrategy):

    MARKET_ID_LOOKUP = "id"

    def __init__(self, local_dir: str, *args, **kwargs):
        BaseStrategy.__init__(self, *args, **kwargs)
        self.local_dir = local_dir
        self.stream_id = create_short_uuid()
        self._loaded_markets = []  # list of marketIds

    def start(self) -> None:
        # check local dir
        if not os.path.isdir(self.local_dir):
            raise OSError("File dir %s does not exist" % self.local_dir)
        # create sub dir
        directory = os.path.join(self.local_dir, self.stream_id)
        if not os.path.exists(directory):
            os.makedirs(directory)

    def process_raw_data(self, publish_time, data):
        filename = "%s" % data.get(self.MARKET_ID_LOOKUP)
        file_directory = os.path.join(self.local_dir, self.stream_id, filename)

        with open(file_directory, "a") as f:
            f.write(
                json.dumps({"op": "mcm", "clk": None, "pt": publish_time, "mc": [data]})
                + "\n"
            )

        if (
            "marketDefinition" in data
            and data["marketDefinition"]["status"] == "CLOSED"
        ):
            self._on_market_closed(data)

    def _on_market_closed(self, data: dict) -> None:
        market_id = data.get(self.MARKET_ID_LOOKUP)
        logger.info("Closing market %s" % market_id)
        if market_id in self._loaded_markets:
            logger.warning(
                "File: /{0}/{1}/{2} has already been loaded, updating..".format(
                    self.local_dir, self.stream_id, market_id
                )
            )

        file_dir = os.path.join(self.local_dir, self.stream_id, market_id)
        market_definition = data.get("marketDefinition")

        # todo check file exists
        # todo check file is not empty

        # zip file
        zip_file_dir = self._zip_file(file_dir, market_id)
        print(zip_file_dir)

        # todo core load code

        # todo clean up

        self._loaded_markets.append(market_id)

    def _zip_file(self, file_dir: str, market_id: str) -> str:
        """zips txt file into filename.zip
        """
        zip_file_directory = os.path.join(
            self.local_dir, self.stream_id, "%s.zip" % market_id
        )
        with zipfile.ZipFile(zip_file_directory, mode="w") as zf:
            zf.write(
                file_dir, os.path.basename(file_dir), compress_type=zipfile.ZIP_DEFLATED
            )
        return zip_file_directory

    @staticmethod
    def _create_metadata(market_definition: dict) -> dict:
        try:
            del market_definition["runners"]
        except KeyError:
            pass
        return dict([a, str(x)] for a, x in market_definition.items())


class S3MarketRecorder(MarketRecorder):
    pass
