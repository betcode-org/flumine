import unittest
from unittest import mock

from flumine import FlumineBacktest
from flumine.clients import ExchangeType
from flumine.order.orderpackage import OrderPackageType
from flumine import config
from flumine.exceptions import RunError


class FlumineBacktestTest(unittest.TestCase):
    def setUp(self):
        self.mock_client = mock.Mock(EXCHANGE=ExchangeType.SIMULATED)
        self.flumine = FlumineBacktest(self.mock_client)

    def test_init(self):
        self.assertTrue(self.flumine.BACKTEST)

    def test_run_error(self):
        mock_client = mock.Mock()
        mock_client.EXCHANGE = 69
        self.flumine.client = mock_client
        with self.assertRaises(RunError):
            self.flumine.run()

    @mock.patch("flumine.backtest.backtest.FlumineBacktest._unpatch_datetime")
    @mock.patch("flumine.backtest.backtest.FlumineBacktest._process_end_flumine")
    @mock.patch("flumine.backtest.backtest.events")
    @mock.patch("flumine.backtest.backtest.FlumineBacktest._process_market_books")
    @mock.patch("flumine.backtest.backtest.FlumineBacktest._monkey_patch_datetime")
    def test_run(
        self,
        mock__monkey_patch_datetime,
        mock__process_market_books,
        mock_events,
        mock__process_end_flumine,
        mock__unpatch_datetime,
    ):
        mock_stream = mock.Mock()
        mock_market_book = mock.Mock()
        mock_gen = mock.Mock(return_value=[[mock_market_book]])
        mock_stream.create_generator.return_value = mock_gen
        self.flumine.streams._streams = [mock_stream]
        self.flumine.run()
        mock__monkey_patch_datetime.assert_called_with()
        mock__process_market_books.assert_called_with(mock_events.MarketBookEvent())
        mock__process_end_flumine.assert_called_with()
        mock__unpatch_datetime.assert_called_with()
        self.assertEqual(mock_market_book.streaming_unique_id, mock_stream.stream_id)

    @mock.patch("flumine.backtest.backtest.FlumineBacktest._process_market_orders")
    @mock.patch("flumine.backtest.backtest.FlumineBacktest._process_backtest_orders")
    @mock.patch("flumine.backtest.backtest.FlumineBacktest._check_pending_packages")
    def test__process_market_books(
        self,
        mock__check_pending_packages,
        mock__process_backtest_orders,
        mock__process_market_orders,
    ):
        mock_event = mock.Mock()
        mock_market_book = mock.Mock(market_id="1.23")
        mock_market_book.runners = []
        mock_market = mock.Mock(market_book=mock_market_book, context={})
        mock_market.blotter.live_orders = []
        self.flumine.markets._markets = {"1.23": mock_market}
        mock_event.event = [mock_market_book]
        self.flumine._process_market_books(mock_event)
        mock__check_pending_packages.assert_called_with()
        mock__process_backtest_orders.assert_called_with(mock_market)
        mock__process_market_orders.assert_called_with()

    @mock.patch("flumine.backtest.backtest.process.process_current_order")
    def test__process_backtest_orders(self, mock_process_current_order):
        mock_market = mock.Mock(context={})
        mock_order = mock.Mock()
        mock_order.trade.status.value = "Complete"
        mock_market.blotter.live_orders = [mock_order]
        self.flumine._process_backtest_orders(mock_market)
        mock_process_current_order.assert_called_with(mock_order)
        mock_market.blotter.complete_order.assert_called_with(mock_order)

    def test__process_backtest_orders_strategies(self):
        mock_market = mock.Mock(context={})
        mock_market.blotter.live_orders = []
        mock_strategy = mock.Mock()
        self.flumine.strategies = [mock_strategy]
        self.flumine._process_backtest_orders(mock_market)
        mock_strategy.process_orders.assert_called_with(
            mock_market, mock_market.blotter.strategy_orders(mock_strategy)
        )

    def test__process_market_orders(self):
        self.flumine._pending_packages = []
        mock_order_package = mock.Mock()
        mock_market = mock.Mock()
        mock_market.blotter.process_orders.return_value = [mock_order_package]
        self.flumine.markets = [mock_market]
        self.flumine._process_market_orders()
        mock_market.blotter.process_orders.assert_called_with(
            self.flumine.client, mock_market.market_book.bet_delay
        )
        self.assertEqual(self.flumine._pending_packages, [mock_order_package])

    @mock.patch("flumine.backtest.backtest.BaseFlumine._process_order_package")
    def test__process_order_package(self, mock__process_order_package):
        mock_order_package = mock.Mock(processed=False)
        self.flumine._process_order_package(mock_order_package)
        self.assertTrue(mock_order_package.processed)

    @mock.patch("flumine.backtest.backtest.FlumineBacktest._process_order_package")
    def test__check_pending_packages_place(self, mock__process_order_package):
        mock_client = mock.Mock()
        mock_client.execution.PLACE_LATENCY = 2.0
        mock_order_package = mock.Mock(
            package_type=OrderPackageType.PLACE,
            elapsed_seconds=5,
            bet_delay=1,
            client=mock_client,
        )
        self.flumine._pending_packages = [mock_order_package]
        self.flumine._check_pending_packages()
        mock__process_order_package.assert_called_with(mock_order_package)

    @mock.patch("flumine.backtest.backtest.FlumineBacktest._process_order_package")
    def test__check_pending_packages_place_pending(self, mock__process_order_package):
        mock_client = mock.Mock()
        mock_client.execution.PLACE_LATENCY = 2.0
        mock_order_package = mock.Mock(
            package_type=OrderPackageType.PLACE,
            elapsed_seconds=2,
            bet_delay=1,
            client=mock_client,
        )
        self.flumine._pending_packages = [mock_order_package]
        self.flumine._check_pending_packages()
        mock__process_order_package.assert_not_called()

    @mock.patch("flumine.backtest.backtest.FlumineBacktest._process_order_package")
    def test__check_pending_packages_cancel(self, mock__process_order_package):
        mock_client = mock.Mock()
        mock_client.execution.CANCEL_LATENCY = 2.0
        mock_order_package = mock.Mock(
            package_type=OrderPackageType.CANCEL, elapsed_seconds=3, client=mock_client
        )
        self.flumine._pending_packages = [mock_order_package]
        self.flumine._check_pending_packages()
        mock__process_order_package.assert_called_with(mock_order_package)

    @mock.patch("flumine.backtest.backtest.FlumineBacktest._process_order_package")
    def test__check_pending_packages_cancel_pending(self, mock__process_order_package):
        mock_client = mock.Mock()
        mock_client.execution.CANCEL_LATENCY = 2.0
        mock_order_package = mock.Mock(
            package_type=OrderPackageType.CANCEL, elapsed_seconds=2, client=mock_client
        )
        self.flumine._pending_packages = [mock_order_package]
        self.flumine._check_pending_packages()
        mock__process_order_package.assert_not_called()

    @mock.patch("flumine.backtest.backtest.FlumineBacktest._process_order_package")
    def test__check_pending_packages_update(self, mock__process_order_package):
        mock_client = mock.Mock()
        mock_client.execution.UPDATE_LATENCY = 2.0
        mock_order_package = mock.Mock(
            package_type=OrderPackageType.UPDATE, elapsed_seconds=3, client=mock_client
        )
        self.flumine._pending_packages = [mock_order_package]
        self.flumine._check_pending_packages()
        mock__process_order_package.assert_called_with(mock_order_package)

    @mock.patch("flumine.backtest.backtest.FlumineBacktest._process_order_package")
    def test__check_pending_packages_update_pending(self, mock__process_order_package):
        mock_client = mock.Mock()
        mock_client.execution.UPDATE_LATENCY = 2.0
        mock_order_package = mock.Mock(
            package_type=OrderPackageType.UPDATE, elapsed_seconds=2, client=mock_client
        )
        self.flumine._pending_packages = [mock_order_package]
        self.flumine._check_pending_packages()
        mock__process_order_package.assert_not_called()

    @mock.patch("flumine.backtest.backtest.FlumineBacktest._process_order_package")
    def test__check_pending_packages_replace(self, mock__process_order_package):
        mock_client = mock.Mock()
        mock_client.execution.REPLACE_LATENCY = 2.0
        mock_order_package = mock.Mock(
            package_type=OrderPackageType.REPLACE,
            elapsed_seconds=5,
            bet_delay=1,
            client=mock_client,
        )
        self.flumine._pending_packages = [mock_order_package]
        self.flumine._check_pending_packages()
        mock__process_order_package.assert_called_with(mock_order_package)

    @mock.patch("flumine.backtest.backtest.FlumineBacktest._process_order_package")
    def test__check_pending_packages_replace_pending(self, mock__process_order_package):
        mock_client = mock.Mock()
        mock_client.execution.REPLACE_LATENCY = 2.0
        mock_order_package = mock.Mock(
            package_type=OrderPackageType.REPLACE,
            elapsed_seconds=2,
            bet_delay=1,
            client=mock_client,
        )
        self.flumine._pending_packages = [mock_order_package]
        self.flumine._check_pending_packages()
        mock__process_order_package.assert_not_called()

    @mock.patch("flumine.baseflumine.BaseFlumine.info")
    @mock.patch("flumine.baseflumine.BaseFlumine.log_control")
    def test__process_close_market_closed(self, mock_log_control, mock_info):
        mock_strategy = mock.Mock()
        mock_strategy.stream_ids = [1, 2, 3]
        self.flumine.strategies = [mock_strategy]
        mock_market = mock.Mock(closed=False, elapsed_seconds_closed=None)
        mock_market.market_book.streaming_unique_id = 2
        self.flumine.markets._markets = {
            "1.23": mock_market,
            "4.56": mock.Mock(market_id="4.56", closed=True, elapsed_seconds_closed=25),
            "7.89": mock.Mock(
                market_id="7.89", closed=True, elapsed_seconds_closed=3601
            ),
            "1.01": mock.Mock(
                market_id="1.01", closed=False, elapsed_seconds_closed=3601
            ),
        }
        mock_event = mock.Mock()
        mock_market_book = mock.Mock(market_id="1.23")
        mock_event.event = mock_market_book
        self.flumine._process_close_market(mock_event)
        self.assertEqual(len(self.flumine.markets._markets), 4)

    def test_str(self):
        assert str(self.flumine) == "<FlumineBacktest>"

    def test_repr(self):
        assert repr(self.flumine) == "<FlumineBacktest>"

    def test_enter_exit(self):
        control = mock.Mock()
        self.flumine._logging_controls = [control]
        self.flumine.simulated_execution = mock.Mock()
        self.flumine.betfair_execution = mock.Mock()
        with self.flumine:
            self.assertTrue(self.flumine._running)
            self.assertTrue(config.simulated)

        self.assertFalse(self.flumine._running)
        self.assertTrue(config.simulated)
        self.flumine.simulated_execution.shutdown.assert_called_with()
        self.flumine.betfair_execution.shutdown.assert_called_with()
        control.start.assert_called_with()

    def tearDown(self) -> None:
        config.simulated = False
