import csv
import os
import json
import datetime
from betfairlightweight.filters import (
    streaming_market_filter,
    streaming_market_data_filter,
)


class BaseRecorder:
    """Base recorder which connects to all
    markets.
    """

    name = 'BASE_RECORDER'

    def __init__(self, market_filter=None, market_data_filter=None):
        self.market_filter = market_filter or streaming_market_filter()
        self.market_data_filter = market_data_filter or streaming_market_data_filter()

    def __call__(self, market_book):
        """Checks market using market book parameters
        function then passes market_book to be processed.

        :param market_book: Market Book object
        """
        if self.market_book_parameters(market_book):
            self.process_market_book(market_book)
        elif market_book.status == 'CLOSED':
            self.on_market_closed(market_book)

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
        pass

    def __str__(self):
        return '<%s>' % self.name


class DataRecorder(BaseRecorder):
    """Data recorder, records data to
    market_id.csv
    """

    name = 'DATA_RECORDER'

    def __init__(self, market_filter, market_data_filter, in_play=None, directory='', seconds_to_start=None):
        super(DataRecorder, self).__init__(market_filter, market_data_filter)
        self.in_play = in_play
        self.directory = directory
        self.seconds_to_start = seconds_to_start

    def market_book_parameters(self, market_book):
        if market_book.status not in ['CLOSED', 'SUSPENDED']:
            if self.in_play is None or market_book.inplay == self.in_play:
                if self.seconds_to_start:
                    seconds_to_start = (
                        market_book.market_definition.market_time - datetime.datetime.utcnow()
                    ).total_seconds()

                    if seconds_to_start < 0:
                        return False
                    elif seconds_to_start < self.seconds_to_start:
                        return True
                else:
                    return True

    def process_market_book(self, market_book):
        filename = '%s.csv' % market_book.market_id
        file_directory = os.path.join(self.directory, filename)

        with open(file_directory, 'a') as outfile:
            writer = csv.writer(outfile, quoting=csv.QUOTE_MINIMAL)
            writer.writerow(
                [market_book.json()]
            )

    def on_market_closed(self, market_book):
        self.process_market_book(market_book)  # last market book will contain results


class StreamRecorder(DataRecorder):
    """Data recorder, records stream data
    to market_id.csv
    """

    name = 'STREAM_RECORDER'

    def process_market_book(self, market_book):
        filename = '%s.csv' % market_book.market_id
        file_directory = os.path.join(self.directory, filename)

        with open(file_directory, 'a') as outfile:
            writer = csv.writer(outfile, quoting=csv.QUOTE_MINIMAL)
            writer.writerow(
                [json.dumps(market_book.streaming_update)]
            )
