

class BaseRecorder:

    name = 'BASE_RECORDER'

    def __init__(self, market_filter, market_data_filter):
        self._market_filter = market_filter
        self._market_data_filter = market_data_filter

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
