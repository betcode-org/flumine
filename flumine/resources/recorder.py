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
    _market_filter = MarketFilter()
    _market_data_filter = MarketDataFilter()

    def __call__(self, market_book):
        """Checks market using market book
        parameters function then passes
        market_book to be processed

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

    @property
    def market_filter(self):
        return self._market_filter.serialise

    @property
    def market_data_filter(self):
        return self._market_data_filter.serialise

    def __str__(self):
        return '<%s>' % self.name


class RacingRecorder(BaseRecorder):
    """Horse Racing data recorder, records
    data to racing_data_yyyy-mm-dd.csv
    """

    name = 'RACING_RECORDER'

    def __init__(self, in_play=False, directory=''):
        self.in_play = in_play
        self.directory = directory

        self._market_filter = MarketFilter(
                event_type_ids=['7'],
                country_codes=['GB', 'IE'],
                market_types=['WIN'],
        )
        self._market_data_filter = MarketDataFilter(
                fields=['EX_BEST_OFFERS', 'EX_TRADED_VOL', 'EX_LTP', 'EX_MARKET_DEF'],
                ladder_levels=1
        )

    def market_book_parameters(self, market_book):
        if market_book.status != 'CLOSED' and market_book.status != 'SUSPENDED' and market_book.inplay == self.in_play:
            return True

    def process_market_book(self, market_book):
        filename = 'racing_data_%s.csv' % datetime.date.today()
        file_directory = os.path.join(self.directory, filename)

        fieldnames = [
            'datetime_created', 'market_id', 'status', 'inplay', 'total_matched',
            'selection_id', 'back', 'lay', 'last_price_traded', 'selection_matched'
        ]
        with open(file_directory, 'a') as f:
            for runner in market_book.runners:
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
