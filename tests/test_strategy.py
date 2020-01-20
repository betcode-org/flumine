import unittest
from unittest import mock

from flumine.strategy import strategy


class StrategiesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.strategies = strategy.Strategies()

    def test_init(self):
        self.assertEqual(self.strategies._strategies, [])

    def test_call(self):
        mock_strategy = mock.Mock()
        self.strategies(mock_strategy)
        self.assertEqual(self.strategies._strategies, [mock_strategy])
        mock_strategy.start.assert_called()

    def test_iter(self):
        for i in self.strategies:
            assert i

    def test_len(self):
        self.assertEqual(len(self.strategies), 0)


class BaseStrategyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_market_filter = mock.Mock()
        self.mock_market_data_filter = mock.Mock()
        self.streaming_timeout = 2
        self.strategy = strategy.BaseStrategy(
            market_filter=self.mock_market_filter,
            market_data_filter=self.mock_market_data_filter,
            streaming_timeout=self.streaming_timeout,
        )

    def test_init(self):
        self.assertEqual(self.strategy.market_filter, self.mock_market_filter)
        self.assertEqual(self.strategy.market_data_filter, self.mock_market_data_filter)
        self.assertEqual(self.strategy.streaming_timeout, self.streaming_timeout)

    def test_start(self):
        self.strategy.start()

    def test_check_market_book(self):
        with self.assertRaises(NotImplementedError):
            self.strategy.check_market_book(None)

    def test_process_market_book(self):
        with self.assertRaises(NotImplementedError):
            self.strategy.process_market_book(None)

    def test_process_race_card(self):
        self.strategy.process_race_card(None)

    def test_process_orders(self):
        self.strategy.process_orders(None)
