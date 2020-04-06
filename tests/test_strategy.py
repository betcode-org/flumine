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
        mock_strategy.add.assert_called_with()

    def test_start(self):
        mock_strategy = mock.Mock()
        self.strategies._strategies.append(mock_strategy)
        self.strategies.start()
        mock_strategy.start.assert_called_with()

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
        self.conflate_ms = 100
        self.strategy = strategy.BaseStrategy(
            market_filter=self.mock_market_filter,
            market_data_filter=self.mock_market_data_filter,
            streaming_timeout=self.streaming_timeout,
            conflate_ms=self.conflate_ms,
            stream_class=strategy.MarketStream,
            name="test",
            context={"trigger": 0.123},
        )

    def test_init(self):
        self.assertEqual(self.strategy.market_filter, self.mock_market_filter)
        self.assertEqual(self.strategy.market_data_filter, self.mock_market_data_filter)
        self.assertEqual(self.strategy.streaming_timeout, self.streaming_timeout)
        self.assertEqual(self.strategy.conflate_ms, self.conflate_ms)
        self.assertEqual(self.strategy.stream_class, strategy.MarketStream)
        self.assertEqual(self.strategy._name, "test")
        self.assertEqual(self.strategy.context, {"trigger": 0.123})

    def test_check_market_no_subscribed(self):
        mock_market = mock.Mock()
        mock_market_book = mock.Mock()
        mock_market_book.streaming_unique_id = 12
        self.assertFalse(self.strategy.check_market(mock_market, mock_market_book))

    @mock.patch(
        "flumine.strategy.strategy.BaseStrategy.stream_ids",
        return_value=[12],
        new_callable=mock.PropertyMock,
    )
    @mock.patch(
        "flumine.strategy.strategy.BaseStrategy.check_market_book", return_value=False
    )
    def test_check_market_check_fail(
        self, mock_check_market_book, mock_market_stream_ids
    ):
        mock_market = mock.Mock()
        mock_market_book = mock.Mock()
        mock_market_book.streaming_unique_id = 12
        self.assertFalse(self.strategy.check_market(mock_market, mock_market_book))
        mock_check_market_book.assert_called_with(mock_market, mock_market_book)
        mock_market_stream_ids.assert_called_with()

    @mock.patch(
        "flumine.strategy.strategy.BaseStrategy.stream_ids",
        return_value=[12],
        new_callable=mock.PropertyMock,
    )
    @mock.patch(
        "flumine.strategy.strategy.BaseStrategy.check_market_book", return_value=True
    )
    def test_check_market_check_pass(
        self, mock_check_market_book, mock_market_stream_ids
    ):
        mock_market = mock.Mock()
        mock_market_book = mock.Mock()
        mock_market_book.streaming_unique_id = 12
        self.assertTrue(self.strategy.check_market(mock_market, mock_market_book))
        mock_check_market_book.assert_called_with(mock_market, mock_market_book)

    def test_add(self):
        self.strategy.add()

    def test_start(self):
        self.strategy.start()

    def test_check_market_book(self):
        self.assertFalse(self.strategy.check_market_book(None, None))

    def test_process_market_book(self):
        self.strategy.process_market_book(None, None)

    def test_process_raw_data(self):
        self.strategy.process_raw_data(None, None)

    def test_process_race_card(self):
        self.strategy.process_race_card(None)

    def test_process_orders(self):
        self.strategy.process_orders(None)

    def test_finish(self):
        self.strategy.finish()

    def test_stream_ids(self):
        mock_stream = mock.Mock()
        mock_stream.stream_id = 321
        self.strategy.streams = [mock_stream]
        self.assertEqual(self.strategy.stream_ids, [321])

    def test_info(self):
        self.assertEqual(
            self.strategy.info,
            {
                "conflate_ms": self.conflate_ms,
                "market_data_filter": self.mock_market_data_filter,
                "market_filter": self.mock_market_filter,
                "name": "test",
                "stream_ids": [],
                "streaming_timeout": self.streaming_timeout,
                "context": {"trigger": 0.123},
            },
        )

    def test_name(self):
        self.assertEqual(self.strategy.name, "test")

    def test_str(self):
        self.assertEqual(str(self.strategy), "test")
