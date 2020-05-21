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
            max_selection_exposure=1,
            max_order_exposure=2,
        )

    def test_init(self):
        self.assertEqual(self.strategy.market_filter, self.mock_market_filter)
        self.assertEqual(self.strategy.market_data_filter, self.mock_market_data_filter)
        self.assertEqual(self.strategy.streaming_timeout, self.streaming_timeout)
        self.assertEqual(self.strategy.conflate_ms, self.conflate_ms)
        self.assertEqual(self.strategy.stream_class, strategy.MarketStream)
        self.assertEqual(self.strategy._name, "test")
        self.assertEqual(self.strategy.context, {"trigger": 0.123})
        self.assertEqual(self.strategy.max_selection_exposure, 1)
        self.assertEqual(self.strategy.max_order_exposure, 2)

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
        self.strategy.process_orders(None, None)

    def test_process_closed_market(self):
        self.strategy.process_closed_market(None, None)

    def test_finish(self):
        self.strategy.finish()

    def test_place_order(self):
        mock_order = mock.Mock()
        mock_order.lookup = ("1", 2, 3)
        mock_market = mock.Mock()
        self.strategy.place_order(mock_market, mock_order)
        mock_market.place_order.assert_called_with(mock_order)
        self.assertIn(mock_order.lookup, self.strategy._invested)

    def test_cancel_order(self):
        mock_order = mock.Mock()
        mock_market = mock.Mock()
        self.strategy.cancel_order(mock_market, mock_order, 0.01)
        mock_market.cancel_order.assert_called_with(mock_order, 0.01)

    def test_update_order(self):
        mock_order = mock.Mock()
        mock_market = mock.Mock()
        self.strategy.update_order(mock_market, mock_order, "PERSIST")
        mock_market.update_order.assert_called_with(mock_order, "PERSIST")

    def test_replace_order(self):
        mock_order = mock.Mock()
        mock_market = mock.Mock()
        self.strategy.replace_order(mock_market, mock_order, 1.01)
        mock_market.replace_order.assert_called_with(mock_order, 1.01)

    def test_validate_order(self):
        mock_order = mock.Mock()
        runner_context = mock.Mock()
        runner_context.invested = False
        self.assertTrue(self.strategy.validate_order(runner_context, mock_order))
        runner_context.invested = True
        self.assertFalse(self.strategy.validate_order(runner_context, mock_order))

    def test_is_invested(self):
        mock_context = mock.Mock(invested=True)
        self.strategy._invested = {("2", 456, 1): mock_context}
        self.assertFalse(self.strategy.is_invested("1", 123, 1.0))
        self.assertFalse(self.strategy.is_invested("2", 123, 1.0))
        self.assertTrue(self.strategy.is_invested("2", 456, 1.0))

    def test_get_runner_context(self):
        mock_context = mock.Mock(invested=True)
        self.strategy._invested = {("2", 456, 0): mock_context}
        self.assertEqual(self.strategy.get_runner_context("2", 456, 0), mock_context)
        self.strategy.get_runner_context("2", 789, 0)
        self.assertEqual(len(self.strategy._invested), 2)

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
                "name_hash": "a94a8fe5ccb19",
                "stream_ids": [],
                "streaming_timeout": self.streaming_timeout,
                "context": {"trigger": 0.123},
            },
        )

    def test_name(self):
        self.assertEqual(self.strategy.name, "test")

    def test_name_hash(self):
        self.assertEqual(self.strategy.name_hash, "a94a8fe5ccb19")

    def test_str(self):
        self.assertEqual(str(self.strategy), "test")
