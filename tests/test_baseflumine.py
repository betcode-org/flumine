import unittest
from unittest import mock

from flumine.baseflumine import BaseFlumine


class BaseFlumineTest(unittest.TestCase):
    def setUp(self):
        self.mock_client = mock.Mock(paper_trade=False)
        self.base_flumine = BaseFlumine(self.mock_client)

    def test_init(self):
        self.assertFalse(self.base_flumine.BACKTEST)
        self.assertEqual(self.base_flumine.client, self.mock_client)
        self.assertFalse(self.base_flumine._running)
        self.assertEqual(self.base_flumine._market_middleware, [])
        self.assertEqual(self.base_flumine._logging_controls, [])
        self.assertEqual(len(self.base_flumine._trading_controls), 2)
        self.assertEqual(self.base_flumine._workers, [])

    @mock.patch("flumine.baseflumine.SimulatedMiddleware")
    @mock.patch("flumine.baseflumine.BaseFlumine.add_market_middleware")
    def test_init_backtest(self, mock_add_market_middleware, mock_SimulatedMiddleware):
        BaseFlumine.BACKTEST = True
        mock_client = mock.Mock(paper_trade=False)
        BaseFlumine(mock_client)
        mock_add_market_middleware.assert_called_with(mock_SimulatedMiddleware())
        BaseFlumine.BACKTEST = False

    @mock.patch("flumine.baseflumine.SimulatedMiddleware")
    @mock.patch("flumine.baseflumine.BaseFlumine.add_market_middleware")
    def test_init_paper_trade(
        self, mock_add_market_middleware, mock_SimulatedMiddleware
    ):
        mock_client = mock.Mock(paper_trade=True)
        BaseFlumine(mock_client)
        mock_add_market_middleware.assert_called_with(mock_SimulatedMiddleware())

    def test_run(self):
        with self.assertRaises(NotImplementedError):
            self.base_flumine.run()

    @mock.patch("flumine.baseflumine.events")
    @mock.patch("flumine.baseflumine.BaseFlumine.log_control")
    def test_add_strategy(self, mock_log_control, mock_events):
        mock_strategy = mock.Mock()
        mock_client = mock.Mock()
        self.base_flumine.add_strategy(mock_strategy, mock_client)
        self.assertEqual(len(self.base_flumine.strategies), 1)
        self.assertEqual(len(self.base_flumine.streams), 1)
        mock_log_control.assert_called_with(mock_events.StrategyEvent(mock_strategy))

    def test_add_worker(self):
        mock_worker = mock.Mock()
        self.base_flumine.add_worker(mock_worker)
        self.assertEqual(len(self.base_flumine._workers), 1)

    def test_add_client_control(self):
        self.mock_client.trading_controls = []
        mock_control = mock.Mock()
        self.base_flumine.add_client_control(mock_control)
        self.assertEqual(
            self.base_flumine.client.trading_controls,
            [mock_control(self.base_flumine, self.mock_client)],
        )

    def test_add_trading_control(self):
        mock_control = mock.Mock()
        self.base_flumine.add_trading_control(mock_control)
        self.assertEqual(len(self.base_flumine._trading_controls), 3)

    def test_add_market_middleware(self):
        mock_middleware = mock.Mock()
        self.base_flumine.add_market_middleware(mock_middleware)
        self.assertEqual(len(self.base_flumine._market_middleware), 1)

    def test_add_logging_control(self):
        mock_control = mock.Mock()
        self.base_flumine.add_logging_control(mock_control)
        self.assertEqual(len(self.base_flumine._logging_controls), 1)

    def test_log_control(self):
        mock_control = mock.Mock()
        self.base_flumine._logging_controls.append(mock_control)
        mock_event = mock.Mock()
        self.base_flumine.log_control(mock_event)
        mock_control.logging_queue.put.assert_called_with(mock_event)

    def test__add_default_workers(self):
        self.base_flumine._add_default_workers()
        self.assertEqual(len(self.base_flumine._workers), 0)

    def test__process_market_books(self):
        mock_event = mock.Mock()
        mock_market_book = mock.Mock(publish_time_epoch=123)
        mock_market_book.runners = []
        mock_event.event = [mock_market_book]
        self.base_flumine._process_market_books(mock_event)

    def test__process_market_orders(self):
        mock_market = mock.Mock()
        mock_market.blotter.process_orders.return_value = [1, 2, 3]
        self.base_flumine.markets = [mock_market]
        self.base_flumine._process_market_orders()
        mock_market.blotter.process_orders.assert_called_with(
            self.mock_client, mock_market.market_book.bet_delay
        )

    def test__process_order_package(self):
        mock_trading_control = mock.Mock()
        self.base_flumine._trading_controls = [mock_trading_control]
        mock_client_trading_control = mock.Mock()
        mock_order_package = mock.Mock()
        mock_order_package.market_id = "1.123"
        mock_order_package.client.trading_controls = [mock_client_trading_control]
        self.base_flumine._process_order_package(mock_order_package)
        mock_order_package.client.execution.handler.assert_called_with(
            mock_order_package
        )
        mock_trading_control.assert_called_with(mock_order_package)
        mock_client_trading_control.assert_called_with(mock_order_package)

    def test__process_order_package_empty(self):
        mock_client_trading_control = mock.Mock()
        mock_order_package = mock.Mock()
        mock_order_package.market_id = "1.123"
        mock_order_package.client.trading_controls = [mock_client_trading_control]
        mock_order_package.info = {}
        mock_order_package.orders = []
        self.base_flumine._trading_controls = []
        self.base_flumine._process_order_package(mock_order_package)
        mock_order_package.client.execution.handler.assert_not_called()

    def test__process_order_package_controls(self):
        mock_trading_control = mock.Mock()
        mock_client_control = mock.Mock()
        self.base_flumine._trading_controls = [mock_trading_control]
        mock_client_trading_control = mock.Mock()
        mock_order_package = mock.Mock()
        mock_order_package.market_id = "1.123"
        mock_order_package.client.trading_controls = [mock_client_trading_control]
        mock_order_package.info = {}
        mock_order_package.orders = []
        mock_order_package.client.trading_controls = [mock_client_control]
        self.base_flumine._process_order_package(mock_order_package)
        mock_order_package.client.execution.handler.assert_not_called()
        mock_trading_control.assert_called_with(mock_order_package)
        mock_client_control.assert_called_with(mock_order_package)

    @mock.patch("flumine.baseflumine.Market")
    def test__add_market(self, mock_market):
        mock_middleware = mock.Mock()
        self.base_flumine._market_middleware = [mock_middleware]
        mock_market_book = mock.Mock()
        self.assertEqual(
            self.base_flumine._add_market("1.234", mock_market_book), mock_market()
        )
        self.assertEqual(len(self.base_flumine.markets._markets), 1)
        mock_middleware.add_market.assert_called_with(mock_market())

    @mock.patch("flumine.baseflumine.BaseFlumine.info")
    def test__remove_market(self, _):
        mock_strategy = mock.Mock()
        self.base_flumine.strategies = [mock_strategy]
        mock_markets = mock.Mock()
        self.base_flumine.markets = mock_markets
        mock_middleware = mock.Mock()
        self.base_flumine._market_middleware = [mock_middleware]
        mock_market = mock.Mock()
        self.base_flumine._remove_market(mock_market)
        mock_markets.remove_market.assert_called_with(mock_market.market_id)
        mock_middleware.remove_market.assert_called_with(mock_market)
        mock_strategy.remove_market.assert_called_with(mock_market.market_id)

    @mock.patch("flumine.baseflumine.BaseFlumine._add_market")
    def test__process_raw_data(self, mock__add_market):
        mock_event = mock.Mock()
        mock_event.event = (12, 12345, [{"id": "1.23"}])
        self.base_flumine._process_raw_data(mock_event)
        mock__add_market.assert_called_with("1.23", None)

    @mock.patch("flumine.baseflumine.events")
    @mock.patch("flumine.baseflumine.BaseFlumine._add_market")
    def test__process_raw_data_closed(self, mock__add_market, mock_events):
        mock_queue = mock.Mock()
        self.base_flumine.handler_queue = mock_queue
        mock_event = mock.Mock()
        mock_event.event = (
            12,
            12345,
            [{"id": "1.23", "marketDefinition": {"status": "CLOSED"}}],
        )
        self.base_flumine._process_raw_data(mock_event)
        mock__add_market.assert_called_with("1.23", None)
        mock_queue.put.assert_called_with(mock_events.CloseMarketEvent())
        self.assertEqual(mock_event.event[2][0]["_stream_id"], mock_event.event[0])

    @mock.patch("flumine.baseflumine.BaseFlumine._add_market")
    def test__process_raw_data_no_id(self, mock__add_market):
        mock_event = mock.Mock()
        mock_event.event = (12, 12345, [{"mid": "1.23"}])
        self.base_flumine._process_raw_data(mock_event)
        mock__add_market.assert_not_called()

    @mock.patch("flumine.baseflumine.events")
    @mock.patch("flumine.baseflumine.BaseFlumine.log_control")
    def test__process_market_catalogue(self, mock_log_control, mock_events):
        mock_market = mock.Mock()
        mock_market.market_catalogue = None
        mock_markets = mock.Mock()
        mock_markets.markets = {"1.23": mock_market}
        self.base_flumine.markets = mock_markets
        mock_market_catalogue = mock.Mock()
        mock_market_catalogue.market_id = "1.23"
        mock_event = mock.Mock()
        mock_event.event = [mock_market_catalogue]
        self.base_flumine._process_market_catalogues(mock_event)
        self.assertEqual(mock_market.market_catalogue, mock_market_catalogue)
        mock_log_control.assert_called_with(mock_events.MarketEvent(mock_market))

    def test__process_current_orders(self):
        mock_event = mock.Mock()
        mock_current_orders = mock.Mock()
        mock_current_orders.orders = []
        mock_event.event = [mock_current_orders]
        self.base_flumine._process_current_orders(mock_event)

    @mock.patch("flumine.baseflumine.BaseFlumine._process_market_orders")
    def test__process_custom_event(self, mock__process_market_orders):
        mock_market = mock.Mock()
        self.base_flumine.markets = [mock_market]
        mock_event = mock.Mock()
        self.base_flumine._process_custom_event(mock_event)
        mock_event.callback.assert_called_with(self.base_flumine, mock_event)
        mock__process_market_orders.assert_called_with()

    @mock.patch("flumine.baseflumine.BaseFlumine.info")
    @mock.patch("flumine.baseflumine.BaseFlumine.log_control")
    def test__process_close_market(self, mock_log_control, mock_info):
        mock_strategy = mock.Mock()
        mock_strategy.stream_ids = [1, 2, 3]
        self.base_flumine.strategies = [mock_strategy]
        mock_market = mock.Mock(closed=False, elapsed_seconds_closed=None)
        self.base_flumine.markets._markets = {"1.23": mock_market}
        mock_event = mock.Mock()
        mock_market_book = mock.Mock(market_id="1.23", streaming_unique_id=2)
        mock_event.event = mock_market_book
        self.base_flumine._process_close_market(mock_event)
        mock_market.close_market.assert_called_with()
        mock_market.blotter.process_closed_market.assert_called_with(mock_market_book)
        mock_strategy.process_closed_market.assert_called_with(
            mock_market, mock_market_book
        )
        mock_log_control.assert_called_with(mock_event)
        self.assertEqual(
            self.base_flumine.cleared_market_queue.get(), mock_market_book.market_id
        )

    @mock.patch("flumine.baseflumine.BaseFlumine.info")
    @mock.patch("flumine.baseflumine.BaseFlumine.log_control")
    def test__process_close_market_datum(self, mock_log_control, mock_info):
        mock_strategy = mock.Mock()
        mock_strategy.stream_ids = [1, 2, 3]
        self.base_flumine.strategies = [mock_strategy]
        mock_market = mock.Mock(closed=False, elapsed_seconds_closed=None)
        self.base_flumine.markets._markets = {"1.23": mock_market}
        mock_event = mock.Mock()
        mock_market_book = {"id": "1.23", "_stream_id": 2}
        mock_event.event = mock_market_book
        self.base_flumine._process_close_market(mock_event)
        mock_market.close_market.assert_called_with()
        mock_market.blotter.process_closed_market.assert_called_with(mock_market_book)
        mock_strategy.process_closed_market.assert_called_with(
            mock_market, mock_market_book
        )
        mock_log_control.assert_called_with(mock_event)
        self.assertEqual(
            self.base_flumine.cleared_market_queue.get(), mock_market_book["id"]
        )

    @mock.patch("flumine.baseflumine.BaseFlumine.info")
    def test__process_close_market_no_market(self, mock_info):
        mock_market = mock.Mock(closed=False, elapsed_seconds_closed=None)
        mock_market.market_book.streaming_unique_id = 2
        self.base_flumine.markets._markets = {"1.23": mock_market}
        mock_event = mock.Mock()
        mock_market_book = mock.Mock(market_id="1.45")
        mock_event.event = mock_market_book
        self.base_flumine._process_close_market(mock_event)
        mock_market.close_market.assert_not_called()

    @mock.patch("flumine.baseflumine.BaseFlumine.info")
    @mock.patch("flumine.baseflumine.BaseFlumine.log_control")
    def test__process_close_market_closed(self, mock_log_control, mock_info):
        mock_strategy = mock.Mock()
        mock_strategy.stream_ids = [1, 2, 3]
        self.base_flumine.strategies = [mock_strategy]
        mock_market = mock.Mock(closed=False, elapsed_seconds_closed=None)
        mock_market.market_book.streaming_unique_id = 2
        self.base_flumine.markets._markets = {
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
        self.base_flumine._process_close_market(mock_event)

        self.assertEqual(len(self.base_flumine.markets._markets), 3)

    @mock.patch("flumine.baseflumine.events")
    @mock.patch("flumine.baseflumine.BaseFlumine._process_cleared_orders")
    @mock.patch("flumine.baseflumine.BaseFlumine.info")
    @mock.patch("flumine.baseflumine.BaseFlumine.log_control")
    def test__process_close_market_closed_paper(
        self, mock_log_control, mock_info, mock__process_cleared_orders, mock_events
    ):
        self.base_flumine.client.paper_trade = True
        mock_strategy = mock.Mock()
        mock_strategy.stream_ids = [1, 2, 3]
        self.base_flumine.strategies = [mock_strategy]
        mock_market = mock.Mock(closed=False, elapsed_seconds_closed=None)
        mock_market.market_book.streaming_unique_id = 2
        self.base_flumine.markets._markets = {
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
        self.base_flumine._process_close_market(mock_event)
        self.assertEqual(len(self.base_flumine.markets._markets), 4)
        mock__process_cleared_orders.assert_called_with(
            mock_events.ClearedOrdersEvent()
        )

    @mock.patch("flumine.baseflumine.events")
    @mock.patch("flumine.baseflumine.BaseFlumine.log_control")
    @mock.patch("flumine.baseflumine.BaseFlumine.info")
    def test__process_cleared_orders(self, mock_info, mock_log_control, mock_events):
        mock_market = mock.Mock()
        mock_market.blotter.process_cleared_orders.return_value = []
        mock_markets = mock.Mock()
        mock_markets.markets = {"1.23": mock_market}
        self.base_flumine.markets = mock_markets
        mock_event = mock.Mock()
        mock_event.event.market_id = "1.23"
        mock_event.event.orders = []
        self.base_flumine._process_cleared_orders(mock_event)
        mock_market.blotter.process_cleared_orders.assert_called_with(mock_event.event)
        mock_log_control.assert_called_with(mock_events.ClearedOrdersMetaEvent())

    @mock.patch("flumine.baseflumine.BaseFlumine.info")
    def test__process_cleared_orders_no_market(self, mock_info):
        mock_market = mock.Mock()
        mock_markets = mock.Mock()
        mock_markets.markets = {"1.23": mock_market}
        self.base_flumine.markets = mock_markets
        mock_event = mock.Mock()
        mock_event.event.market_id = "1.24"
        mock_event.event.orders = []
        self.base_flumine._process_cleared_orders(mock_event)
        mock_market.blotter.process_cleared_orders.assert_not_called()

    def test__process_cleared_markets(self):
        mock_event = mock.Mock()
        mock_event.event.orders = []
        self.base_flumine._process_cleared_markets(mock_event)

    def test__process_end_flumine(self):
        self.base_flumine._process_end_flumine()

    def test_info(self):
        self.assertTrue(self.base_flumine.info)

    @mock.patch("flumine.baseflumine.events")
    @mock.patch("flumine.baseflumine.BaseFlumine.log_control")
    def test_enter_exit(self, mock_log_control, mock_events):
        control = mock.Mock()
        self.base_flumine._logging_controls = [control]
        self.base_flumine.simulated_execution = mock.Mock()
        self.base_flumine.betfair_execution = mock.Mock()
        with self.base_flumine:
            self.assertTrue(self.base_flumine._running)
            self.mock_client.login.assert_called_with()

        self.assertFalse(self.base_flumine._running)
        self.mock_client.logout.assert_called_with()
        self.base_flumine.simulated_execution.shutdown.assert_called_with()
        self.base_flumine.betfair_execution.shutdown.assert_called_with()
        control.start.assert_called_with()
        mock_log_control.assert_called_with(mock_events.TerminationEvent(None))
