import unittest
from unittest import mock

from flumine.strategies.basestrategy import BaseStrategy


class BaseStrategyTest(unittest.TestCase):

    def setUp(self):
        self.base_strategy = BaseStrategy()

    def test_init(self):
        assert self.base_strategy.name == 'BASE_STRATEGY'

    @mock.patch('flumine.strategies.basestrategy.BaseStrategy.process_market_book')
    @mock.patch('flumine.strategies.basestrategy.BaseStrategy.market_book_parameters')
    def test_call(self, mock_market_book_parameters, mock_process_market_book):
        mock_market_book = mock.Mock()
        self.base_strategy(mock_market_book)

        mock_market_book_parameters.assert_called_with(mock_market_book)
        mock_process_market_book.assert_called_with(mock_market_book)

    def test_market_book_parameters(self):
        mock_market_book = mock.Mock()
        assert self.base_strategy.market_book_parameters(mock_market_book) is True

    def test_process_market_book(self):
        with self.assertRaises(NotImplementedError):
            mock_market_book = mock.Mock()
            self.base_strategy.process_market_book(mock_market_book)

    def test_str(self):
        assert str(self.base_strategy) == '<BASE_STRATEGY>'
