import unittest
from unittest import mock

from flumine import FlumineBacktest
from flumine.order.orderpackage import OrderPackageType
from flumine import config
from flumine.exceptions import RunError


class FlumineBacktestTest(unittest.TestCase):
    def setUp(self):
        self.mock_trading = mock.Mock()
        self.flumine = FlumineBacktest(self.mock_trading)

    def test_init(self):
        self.assertTrue(self.flumine.BACKTEST)

    def test_run_error(self):
        mock_client = mock.Mock()
        mock_client.EXCHANGE = 69
        self.flumine.client = mock_client
        with self.assertRaises(RunError):
            self.flumine.run()

    # @mock.patch("flumine.flumine.Flumine._process_end_flumine")
    # @mock.patch("flumine.flumine.Flumine._process_raw_data")
    # @mock.patch("flumine.flumine.Flumine._process_market_books")
    # def test_run(
    #     self,
    #     mock__process_market_books,
    #     mock__process_raw_data,
    #     mock__process_end_flumine,
    # ):
    #     events = [
    #         event.MarketCatalogueEvent(None),
    #         event.MarketBookEvent(None),
    #         event.RawDataEvent(None),
    #         event.CurrentOrdersEvent(None),
    #         event.ClearedMarketsEvent(None),
    #         event.ClearedOrdersEvent(None),
    #         event.CloseMarketEvent(None),
    #         event.StrategyResetEvent(None),
    #         event.CustomEvent(None),
    #         event.NewDayEvent(None),
    #         event.EventType.TERMINATOR,
    #     ]
    #     for i in events:
    #         self.flumine.handler_queue.put(i)
    #     self.flumine.run()
    #
    #     mock__process_market_books.assert_called_with(events[1])
    #     mock__process_raw_data.assert_called_with(events[2])
    #     mock__process_end_flumine.assert_called_with()

    @mock.patch("flumine.backtest.backtest.FlumineBacktest._check_pending_packages")
    def test__process_market_books(self, mock__check_pending_packages):
        mock_event = mock.Mock()
        mock_market_book = mock.Mock()
        mock_market_book.runners = []
        mock_event.event = [mock_market_book]
        self.flumine._process_market_books(mock_event)
        mock__check_pending_packages.assert_called_with()

    def test__process_market_orders(self):
        self.flumine._pending_packages = []
        mock_order_package = mock.Mock()
        mock_market = mock.Mock()
        mock_market.blotter.process_orders.return_value = [mock_order_package]
        self.flumine._process_market_orders(mock_market)
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
