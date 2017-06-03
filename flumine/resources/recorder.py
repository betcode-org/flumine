import os
import json
import logging
from betfairlightweight.filters import (
    streaming_market_filter,
    streaming_market_data_filter,
)


class BaseRecorder:
    """Base recorder which connects to all
    markets.
    """

    NAME = 'BASE_RECORDER'

    def __init__(self, storage_engine, market_filter=None, market_data_filter=None):
        self.storage_engine = storage_engine
        self.market_filter = market_filter or streaming_market_filter()
        self.market_data_filter = market_data_filter or streaming_market_data_filter()

    def __call__(self, market_book):
        """Checks market using market book parameters
        function then passes market_book to be processed.

        :param market_book: Market Book object
        """
        if self.market_book_parameters(market_book):
            self.process_market_book(market_book)

    def market_book_parameters(self, market_book):
        """Logic used to decide if market_book should
        be processed

        :param market_book: Market Book object
        :return: True if market is to be processed
        """
        return True

    def process_market_book(self, market_book):
        """Function that processes market book

        :param market_book: Market Book object
        """
        raise NotImplementedError

    def on_market_closed(self, market_book):
        """Function run when market is closed.
        """
        market_id = market_book.get('id')
        market_definition = market_book.get('marketDefinition')
        logging.info('Closing market %s' % market_id)
        self.storage_engine(market_id, market_definition)

    def __str__(self):
        return '<%s>' % self.NAME


class StreamRecorder(BaseRecorder):
    """Data recorder, records stream data
    to /tmp/market_id
    """

    NAME = 'STREAM_RECORDER'

    def process_market_book(self, market_book):
        for market in market_book.get('mc'):
            filename = '%s' % market.get('id')
            file_directory = os.path.join('/tmp', filename)

            with open(file_directory, 'a') as outfile:
                outfile.write(
                    json.dumps(market_book) + '\n'
                )

            if 'marketDefinition' in market and market['marketDefinition']['status'] == 'CLOSED':
                self.on_market_closed(market)
