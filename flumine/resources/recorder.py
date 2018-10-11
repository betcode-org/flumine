import os
import json
import logging
from betfairlightweight.filters import (
    streaming_market_filter,
    streaming_market_data_filter,
)

from ..utils import create_short_uuid
from ..flumine import FLUMINE_DATA

logger = logging.getLogger(__name__)


class BaseRecorder:
    """Base recorder which connects to all
    markets by default.
    """

    NAME = 'BASE_RECORDER'
    STREAM_TYPE = None
    MARKET_ID_LOOKUP = None
    HOST = None

    def __init__(self, storage_engine, market_filter=None, market_data_filter=None):
        self.storage_engine = storage_engine
        self.market_filter = market_filter or streaming_market_filter()
        self.market_data_filter = market_data_filter or streaming_market_data_filter(
            fields=[
                'EX_ALL_OFFERS', 'EX_TRADED', 'EX_TRADED_VOL', 'EX_LTP', 'EX_MARKET_DEF', 'SP_TRADED', 'SP_PROJECTED'
            ]
        )
        self.stream_id = create_short_uuid()  # used to differentiate markets /<FLUMINE_DATA>/<stream_id>
        self.live_markets = []  # list of markets to be processed
        self._setup()
        logger.info('Recorder created %s' % self.stream_id)

    def __call__(self, updates, publish_time):
        """Checks market using market book parameters
        function then passes market_book to be processed.

        :param updates: List of updates
        :param publish_time: Publish time of market book
        """
        for update in updates:
            market_id = update.get(self.MARKET_ID_LOOKUP)
            self.check_market_book(market_id, update)
            if market_id in self.live_markets:
                self.process_update(update, publish_time)

    def check_market_book(self, market_id, market_book):
        """Logic used to decide if market_book should
        be processed

        :param market_id: Market id
        :param market_book: Market Book object
        """
        if market_id not in self.live_markets:
            self.live_markets.append(market_id)

    def process_update(self, update, publish_time):
        """Function that processes update

        :param update: update object
        :param publish_time: Publish time of market book
        """
        raise NotImplementedError

    def on_market_closed(self, update):
        """Function run when market is closed, this
        may execute more than once if update received
        after being closed.
        """
        market_id = update.get(self.MARKET_ID_LOOKUP)
        market_definition = update.get('marketDefinition')
        logger.info('Closing market %s' % market_id)
        self.storage_engine(market_id, market_definition, self.stream_id)

    def _setup(self):
        """Create stream folder in <FLUMINE_DATA>
        """
        directory = os.path.join(FLUMINE_DATA, self.stream_id)
        if not os.path.exists(directory):
            os.makedirs(directory)

    def __str__(self):
        return '<%s>' % self.NAME


class MarketRecorder(BaseRecorder):
    """Data recorder, records stream data
    to /<FLUMINE_DATA>/<stream_id>/market_id,
    a single market per file.
    """

    NAME = 'MARKET_RECORDER'
    STREAM_TYPE = 'market'
    MARKET_ID_LOOKUP = 'id'

    def process_update(self, market_book, publish_time):
        filename = '%s' % market_book.get(self.MARKET_ID_LOOKUP)
        file_directory = os.path.join(FLUMINE_DATA, self.stream_id, filename)

        with open(file_directory, 'a') as outfile:
            outfile.write(
                json.dumps({
                    "op": "mcm",
                    "clk": None,
                    "pt": publish_time,
                    "mc": [market_book]
                }) + '\n'
            )

        if 'marketDefinition' in market_book and market_book['marketDefinition']['status'] == 'CLOSED':
            self.on_market_closed(market_book)


class RaceRecorder(BaseRecorder):

    NAME = 'RACE_RECORDER'
    STREAM_TYPE = 'race'
    MARKET_ID_LOOKUP = 'mid'
    HOST = 'race'

    def process_update(self, update, publish_time):
        filename = '%s' % update.get(self.MARKET_ID_LOOKUP)
        file_directory = os.path.join(FLUMINE_DATA, self.stream_id, filename)

        with open(file_directory, 'a') as outfile:
            outfile.write(
                json.dumps({
                    "op": "rcm",
                    "clk": None,
                    "pt": publish_time,
                    "rc": [update]
                }) + '\n'
            )

        # todo validate this is correct
        if 'rpc' in update:
            rpc = update['rpc']
            if rpc['g'] == 'Finish' and rpc['prg'] == 0 and rpc['ord'] == [] and 'rrc' not in update:
                self.on_market_closed(update)
