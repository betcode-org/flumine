import csv
import os
import datetime
from betfairlightweight.utils import price_check

from .marketfilters import MarketFilter, MarketDataFilter


class BaseRecorder:
    """Base recorder which connects to all
    markets.
    """

    name = 'BASE_RECORDER'

    def __init__(self, market_filter=None, market_data_filter=None):
        self._market_filter = market_filter or MarketFilter()
        self._market_data_filter = market_data_filter or MarketDataFilter()

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
        pass

    @property
    def market_filter(self):
        return self._market_filter.serialise

    @property
    def market_data_filter(self):
        return self._market_data_filter.serialise

    def __str__(self):
        return '<%s>' % self.name


class DataRecorder(BaseRecorder):
    """Data recorder, records data to
    data_yyyy-mm-dd.csv
    """

    name = 'DATA_RECORDER'

    def __init__(self, market_filter, market_data_filter, in_play=False, directory=''):
        super(DataRecorder, self).__init__(market_filter, market_data_filter)
        self.in_play = in_play
        self.directory = directory

    def market_book_parameters(self, market_book):
        if market_book.status != 'CLOSED' and market_book.status != 'SUSPENDED' and market_book.inplay == self.in_play:
            return True

    def process_market_book(self, market_book):
        filename = 'data_%s.csv' % datetime.date.today()
        file_directory = os.path.join(self.directory, filename)

        fieldnames = [
            'datetime_created', 'market_id', 'status', 'inplay', 'total_matched',
            'selection_id', 'back', 'lay', 'last_price_traded', 'selection_matched'
        ]
        with open(file_directory, 'a') as f:
            for runner in market_book.runners:
                if runner.status == 'ACTIVE':
                    csv_writer = csv.DictWriter(f, delimiter=',', fieldnames=fieldnames)
                    csv_writer.writerow(self.serialise_market_book(market_book, runner))

    @staticmethod
    def serialise_market_book(market_book, runner):
        return {
            'datetime_created': market_book.datetime_created,
            'market_id': market_book.market_id,
            'total_matched': market_book.total_matched,
            'status': market_book.status,
            'inplay': market_book.inplay,
            'selection_id': runner.selection_id,
            'back': price_check(runner.ex.available_to_back, 0, 'price'),
            'lay': price_check(runner.ex.available_to_lay, 0, 'price'),
            'last_price_traded': runner.last_price_traded,
            'selection_matched': runner.total_matched,
        }


class MarketBookRecorder(DataRecorder):
    """MarketBook recorder, records market_book
    to market_id.csv
    """

    name = 'MARKET_BOOK_RECORDER'

    def process_market_book(self, market_book):
        filename = '%s.csv' % market_book.market_id
        file_directory = os.path.join(self.directory, filename)

        with open(file_directory, 'a') as outfile:
            writer = csv.writer(outfile, quoting=csv.QUOTE_MINIMAL)
            writer.writerow([market_book.json()])

    def on_market_closed(self, market_book):
        self.process_market_book(market_book)
