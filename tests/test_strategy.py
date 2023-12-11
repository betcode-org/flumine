import unittest
from unittest import mock

from flumine.strategy import strategy
from flumine.strategy.runnercontext import RunnerContext


class RunnerContextMock(RunnerContext):
    """
    A mock class for RunnerContext which maintains most of its properties
    except placed_elapsed_seconds and reset_elapsed_seconds, which are replaced
    with attributes.
    """

    # Properties cannot be replaced with attributes on instances because the
    # assignment invokes a setter, but they can be replaced on a class level
    placed_elapsed_seconds = None
    reset_elapsed_seconds = None

    def __init__(
        self,
        completed_trades: list = [],
        live_trades: list = [],
        placed_elapsed_seconds: float = None,
        reset_elapsed_seconds: float = None,
    ):
        super().__init__(12345678)  # Use dummy selection id
        all_trades = completed_trades + live_trades
        if len(set(all_trades)) != len(all_trades):
            raise ValueError("All trade ids must be unique.")
        for trade_id in all_trades:
            self.place(trade_id)
        for trade_id in completed_trades:
            self.reset(trade_id)
        self.placed_elapsed_seconds = placed_elapsed_seconds
        self.reset_elapsed_seconds = reset_elapsed_seconds


class StrategiesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.strategies = strategy.Strategies()

    def test_init(self):
        self.assertEqual(self.strategies._strategies, [])

    def test_call(self):
        mock_strategy = mock.Mock()
        mock_clients = mock.Mock()
        mock_flumine = mock.Mock()
        self.strategies(mock_strategy, mock_clients, mock_flumine)
        self.assertEqual(self.strategies._strategies, [mock_strategy])
        mock_strategy.add.assert_called_with(mock_flumine)
        self.assertEqual(mock_strategy.clients, mock_clients)

    def test_start(self):
        mock_strategy = mock.Mock()
        mock_flumine = mock.Mock()
        self.strategies._strategies.append(mock_strategy)
        self.strategies.start(mock_flumine)
        mock_strategy.start.assert_called_with(mock_flumine)

    @mock.patch("flumine.strategy.strategy.logger")
    def test_deprecated_calls(self, mock_logger: mock.Mock):
        """
        Tests backwards compatibility with the old call signatures
        of add() and start() methods of BaseStreategy. This test may
        be removed in the future together with the deprecation warning.
        """
        mock_clients = mock.Mock()
        mock_flumine = mock.Mock()
        old_base_strategy = strategy.BaseStrategy({})
        old_base_strategy.add = lambda: None  # Mimic old call signature
        old_base_strategy.start = lambda: None  # Mimic old call signature
        mock_strategy = mock.Mock(wraps=old_base_strategy)
        # Old add() implementation
        self.strategies(mock_strategy, mock_clients, mock_flumine)
        mock_logger.warning.assert_called()  # User warned
        mock_strategy.add.assert_called_with()  # Called with the old signature
        # Old start() implementation
        mock_logger.reset_mock()
        self.strategies.start(mock_flumine)
        mock_logger.warning.assert_called()  # User warned
        mock_strategy.start.assert_called_with()  # Called with the old signature

    def test_finish(self):
        mock_flumine = mock.Mock()
        mock_strategy = mock.Mock()
        self.strategies._strategies.append(mock_strategy)
        self.strategies.finish(mock_flumine)
        mock_strategy.finish.assert_called_with(mock_flumine)

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
            sports_data_filter=["cricketSubscription"],
            streaming_timeout=self.streaming_timeout,
            conflate_ms=self.conflate_ms,
            stream_class=strategy.MarketStream,
            name="test",
            context={"trigger": 0.123},
            max_selection_exposure=1,
            max_order_exposure=2,
            max_trade_count=5,
            max_live_trade_count=3,
            multi_order_trades=False,
        )

    def test_init(self):
        self.assertEqual(self.strategy.market_filter, self.mock_market_filter)
        self.assertEqual(self.strategy.market_data_filter, self.mock_market_data_filter)
        self.assertEqual(self.strategy.sports_data_filter, ["cricketSubscription"])
        self.assertEqual(self.strategy.streaming_timeout, self.streaming_timeout)
        self.assertEqual(self.strategy.conflate_ms, self.conflate_ms)
        self.assertEqual(self.strategy.stream_class, strategy.MarketStream)
        self.assertEqual(self.strategy._name, "test")
        self.assertEqual(self.strategy.context, {"trigger": 0.123})
        self.assertEqual(self.strategy.max_selection_exposure, 1)
        self.assertEqual(self.strategy.max_order_exposure, 2)
        self.assertIsNone(self.strategy.clients)
        self.assertEqual(self.strategy.max_trade_count, 5)
        self.assertEqual(self.strategy.max_live_trade_count, 3)
        self.assertEqual(self.strategy.streams, [])
        self.assertEqual(self.strategy.historic_stream_ids, set())
        self.assertEqual(self.strategy.name_hash, "a94a8fe5ccb19")
        self.assertFalse(self.strategy.multi_order_trades)
        self.assertEqual(strategy.STRATEGY_NAME_HASH_LENGTH, 13)
        self.assertEqual(
            strategy.DEFAULT_MARKET_DATA_FILTER,
            {
                "fields": [
                    "EX_ALL_OFFERS",
                    "EX_TRADED",
                    "EX_TRADED_VOL",
                    "EX_LTP",
                    "EX_MARKET_DEF",
                    "SP_TRADED",
                    "SP_PROJECTED",
                ]
            },
        )

    def test_add(self):
        mock_flumine = mock.Mock()
        self.strategy.add(mock_flumine)

    def test_start(self):
        mock_flumine = mock.Mock()
        self.strategy.start(mock_flumine)

    def test_process_new_market(self):
        self.strategy.process_new_market(None, None)

    def test_check_market_book(self):
        self.assertFalse(self.strategy.check_market_book(None, None))

    def test_process_market_book(self):
        self.strategy.process_market_book(None, None)

    def test_process_market_catalogue(self):
        self.strategy.process_market_catalogue(None, None)

    def test_check_sports_data(self):
        self.assertFalse(self.strategy.check_sports_data(None, None))

    def test_process_sports_data(self):
        self.strategy.process_sports_data(None, None)

    def test_process_raw_data(self):
        self.strategy.process_raw_data(None, None, None)

    def test_process_orders(self):
        self.strategy.process_orders(None, None)

    def test_process_closed_market(self):
        self.strategy.process_closed_market(None, None)

    def test_finish(self):
        self.strategy.finish(mock.Mock())

    def test_remove_market(self):
        self.strategy._invested = {
            ("1.23", 456, 7): 1,
            ("1.23", 891, 7): 2,
            ("1.24", 112, 7): 3,
        }
        self.strategy.remove_market("1.23")
        self.assertEqual(self.strategy._invested, {("1.24", 112, 7): 3})

    def test_validate_order(self):
        mock_order = mock.Mock()
        mock_order.trade.id = "99"  # Unused trade id, nonexistent in runner_context
        # No orders/trades placed yet
        runner_context = RunnerContextMock()
        self.strategy.log_validation = True
        self.assertTrue(self.strategy.validate_order(runner_context, mock_order))
        # trade count (5 is limit)
        runner_context = RunnerContextMock(["1", "2", "3", "4", "5"])
        self.assertFalse(self.strategy.validate_order(runner_context, mock_order))
        # live trade count (3 is limit)
        runner_context = RunnerContextMock([], ["3", "4", "5"])
        self.assertFalse(self.strategy.validate_order(runner_context, mock_order))
        # place elapsed
        runner_context = RunnerContextMock(
            live_trades=["1"], placed_elapsed_seconds=0.49
        )
        mock_order.trade.place_reset_seconds = 0.5
        self.assertFalse(self.strategy.validate_order(runner_context, mock_order))
        # reset elapsed
        runner_context = RunnerContextMock(
            completed_trades=["1"], placed_elapsed_seconds=1, reset_elapsed_seconds=0.49
        )
        mock_order.trade.reset_seconds = 0.5
        self.assertFalse(self.strategy.validate_order(runner_context, mock_order))

    def test_validate_order_reuse_completed_trade(self):
        """Reusing a completed Trade object to place a new order."""
        mock_order = mock.Mock()
        mock_order.trade.id = "1"  # Reuse completed trade
        # trade count - at the limit (5)
        runner_context = RunnerContextMock(["1", "2", "3", "4", "5"])
        self.assertTrue(self.strategy.validate_order(runner_context, mock_order))
        # live trade count- at the limit (3)
        runner_context = RunnerContextMock(["1"], ["3", "4", "5"])
        self.assertFalse(self.strategy.validate_order(runner_context, mock_order))
        # trade count - over the limit (>5) (force=True was used)
        runner_context = RunnerContextMock(["1", "2", "3", "4", "5", "6"])
        self.assertFalse(self.strategy.validate_order(runner_context, mock_order))
        # live trade count- over the limit (>3) (force=True was used)
        runner_context = RunnerContextMock(["1"], ["3", "4", "5", "6"])
        self.assertFalse(self.strategy.validate_order(runner_context, mock_order))

    def test_validate_order_reuse_live_trade(self):
        """Reusing a live Trade object to place a new order."""
        mock_order = mock.Mock()
        mock_order.trade.id = "5"  # Reuse live trade
        # trade count - at the limit (5)
        runner_context = RunnerContextMock(["1", "2", "3"], ["4", "5"])
        self.assertTrue(self.strategy.validate_order(runner_context, mock_order))
        # live trade count - at the limit (3)
        runner_context = RunnerContextMock([], ["3", "4", "5"])
        self.assertTrue(self.strategy.validate_order(runner_context, mock_order))
        # trade count - over the limit (>5) (force=True was used)
        runner_context = RunnerContextMock(["1", "2", "3", "4"], ["5", "6"])
        self.assertFalse(self.strategy.validate_order(runner_context, mock_order))
        # live trade count- over the limit (>3) (force=True was used)
        runner_context = RunnerContextMock([], ["3", "4", "5", "6"])
        self.assertFalse(self.strategy.validate_order(runner_context, mock_order))

    def test_validate_order_multi(self):
        mock_order = mock.Mock()
        mock_order.trade.id = "6"  # In live trades
        runner_context = RunnerContextMock([], ["1", "2", "3", "4", "5", "6"])
        self.assertFalse(self.strategy.validate_order(runner_context, mock_order))
        self.strategy.multi_order_trades = True
        self.assertTrue(self.strategy.validate_order(runner_context, mock_order))

    def test_executable_orders(self):
        mock_context = mock.Mock(executable_orders=True)
        self.strategy._invested = {("2", 456, 1): mock_context}
        self.assertFalse(self.strategy.has_executable_orders("1", 123, 1.0))
        self.assertFalse(self.strategy.has_executable_orders("2", 123, 1.0))
        self.assertTrue(self.strategy.has_executable_orders("2", 456, 1.0))

    def test_get_runner_context(self):
        mock_context = mock.Mock(invested=True)
        self.strategy._invested = {("2", 456, 0): mock_context}
        self.assertEqual(self.strategy.get_runner_context("2", 456, 0), mock_context)
        self.strategy.get_runner_context("2", 789, 0)
        self.assertEqual(len(self.strategy._invested), 2)

    def test_market_cached(self):
        # This is not a good test as it relies too much on implementation details.
        # There is an integration test as well to cover a more realistic use-case.
        mock_stream = mock.Mock()
        mock_stream._listener.stream._caches = {"1.234": None}
        self.strategy.streams = [mock_stream]
        self.assertTrue(self.strategy.market_cached("1.234"))
        self.assertFalse(self.strategy.market_cached("1.789"))

    def test_market_cached_stream_not_registered(self):
        """
        Tests that strategy.market_cached() does not throw an error when called
        on a stream which had not been registered yet
        (betfairlightweight.BaseListener.register_stream not called).
        """
        mock_stream = mock.Mock()
        mock_stream._listener.stream = None
        self.strategy.streams = [mock_stream]
        self.assertFalse(self.strategy.market_cached("1.234"))
        self.assertFalse(self.strategy.market_cached("1.789"))

    def test_stream_ids(self):
        mock_stream = mock.Mock(stream_id=321)
        self.strategy.streams = [mock_stream]
        self.assertEqual(self.strategy.stream_ids, [321])
        self.strategy.historic_stream_ids.add(123)
        self.assertEqual(self.strategy.stream_ids, {123})

    def test_info(self):
        self.assertEqual(
            self.strategy.info,
            {
                "conflate_ms": self.conflate_ms,
                "market_data_filter": self.mock_market_data_filter,
                "market_filter": self.mock_market_filter,
                "strategy_name": "test",
                "name_hash": "a94a8fe5ccb19",
                "stream_ids": [],
                "streaming_timeout": self.streaming_timeout,
                "context": {"trigger": 0.123},
                "max_live_trade_count": 3,
                "max_order_exposure": 2,
                "max_selection_exposure": 1,
                "max_trade_count": 5,
            },
        )

    def test_name(self):
        self.assertEqual(self.strategy.name, "test")

    def test_str(self):
        self.assertEqual(str(self.strategy), "test")
