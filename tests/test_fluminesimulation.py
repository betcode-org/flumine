import unittest
from unittest import mock

from flumine import FlumineSimulation
from flumine.clients import ExchangeType
from flumine.order.orderpackage import OrderPackageType
from flumine import config
from flumine.exceptions import RunError
from flumine.order.trade import TradeStatus
from flumine.markets.blotter import Blotter
from flumine.order.order import OrderTypes
from flumine.markets.market import Market


class FlumineSimulationTest(unittest.TestCase):
    def setUp(self):
        self.mock_client = mock.Mock(EXCHANGE=ExchangeType.SIMULATED)
        self.flumine = FlumineSimulation(self.mock_client)

    def test_init(self):
        self.assertTrue(self.flumine.SIMULATED)
        self.assertEqual(self.flumine.handler_queue, [])

    def test_run_error(self):
        self.flumine.clients._clients.clear()
        mock_client = mock.Mock(EXCHANGE=ExchangeType.BETFAIR, paper_trade=False)
        self.flumine.add_client(mock_client)
        with self.assertRaises(RunError):
            self.flumine.run()

    @mock.patch("flumine.simulation.simulation.FlumineSimulation._process_end_flumine")
    @mock.patch("flumine.simulation.simulation.events")
    @mock.patch("flumine.simulation.simulation.FlumineSimulation._process_market_books")
    def test_run(
        self,
        mock__process_market_books,
        mock_events,
        mock__process_end_flumine,
    ):
        mock_stream = mock.Mock(event_processing=False)
        mock_market_book = mock.Mock()
        mock_gen = mock.Mock(return_value=[[mock_market_book]])
        mock_stream.create_generator.return_value = mock_gen
        self.flumine.streams._streams = [mock_stream]
        self.flumine.run()
        mock__process_market_books.assert_called_with(mock_events.MarketBookEvent())
        mock__process_end_flumine.assert_called_once_with()

    @mock.patch("flumine.simulation.simulation.FlumineSimulation._process_end_flumine")
    @mock.patch("flumine.simulation.simulation.events")
    @mock.patch("flumine.simulation.simulation.FlumineSimulation._process_market_books")
    def test_run_event(
        self,
        mock__process_market_books,
        mock_events,
        mock__process_end_flumine,
    ):
        mock_stream_one = mock.Mock(event_processing=True, event_id=123)
        mock_market_book_one = mock.Mock(publish_time_epoch=321)
        mock_gen_one = mock.Mock(return_value=iter([[mock_market_book_one]]))
        mock_stream_one.create_generator.return_value = mock_gen_one

        mock_stream_two = mock.Mock(event_processing=True, event_id=123)
        mock_market_book_two = mock.Mock(publish_time_epoch=123)
        mock_gen_two = mock.Mock(return_value=iter([[mock_market_book_two]]))
        mock_stream_two.create_generator.return_value = mock_gen_two

        self.flumine.streams._streams = [mock_stream_one, mock_stream_two]
        self.flumine.run()
        mock__process_market_books.assert_called_with(mock_events.MarketBookEvent())
        mock__process_end_flumine.assert_called_once_with()

    @mock.patch(
        "flumine.simulation.simulation.FlumineSimulation._process_simulated_orders"
    )
    @mock.patch(
        "flumine.simulation.simulation.FlumineSimulation._check_pending_packages"
    )
    def test__process_market_books(
        self,
        mock__check_pending_packages,
        mock__process_simulated_orders,
    ):
        self.flumine.handler_queue.append(mock.Mock())
        mock_event = mock.Mock()
        mock_market_book = mock.Mock(market_id="1.23")
        mock_market_book.runners = []
        mock_market = mock.Mock(market_book=mock_market_book, context={})
        mock_market.blotter.live_orders = []
        self.flumine.markets._markets = {"1.23": mock_market}
        mock_event.event = [mock_market_book]
        self.flumine._process_market_books(mock_event)
        mock__check_pending_packages.assert_called_with("1.23")
        mock__process_simulated_orders.assert_called_with(mock_market)

    def test__process_market_books_new_market(self):
        mock_strategy = mock.Mock(stream_ids=[1])
        self.flumine.add_strategy(mock_strategy)
        mock_market_book = mock.Mock(
            market_id="1.23", streaming_unique_id=1, runners=[]
        )
        mock_event = mock.Mock(event=[mock_market_book])
        for call_count in range(1, 5):
            # process_new_market must be called only once, the first time
            with self.subTest(call_count=call_count):
                self.flumine._process_market_books(mock_event)
                mock_strategy.process_new_market.assert_called_once()
                self.assertEqual(
                    mock_strategy.process_market_book.call_count, call_count
                )
        market, market_book = mock_strategy.process_new_market.call_args[0]
        self.assertIs(market_book, mock_market_book)
        self.assertIsInstance(market, Market)
        self.assertIs(market.market_book, mock_market_book)

    def test__process_market_stream_not_subscribed(self):
        """
        Market book should only be called with objects from the streams
        it is subscribed to.
        """
        mock_strategy = mock.Mock(stream_ids=[1, 2])
        self.flumine.add_strategy(mock_strategy)
        mock_market_book = mock.Mock(
            market_id="1.123", streaming_unique_id=5, runners=[]
        )
        mock_event = mock.Mock(event=[mock_market_book])
        self.flumine._process_market_books(mock_event)
        mock_strategy.process_new_market.assert_not_called()
        mock_strategy.check_market_book.assert_not_called()
        mock_strategy.process_market_book.assert_not_called()

    def test__process_market_books_check_market_books(self):
        """
        Tests base_flumine._process_market_books() with different return values
        of strategy.check_market_book().
        """
        mock_strategy = mock.Mock(stream_ids=[1])
        check_pattern = (False, True, True, False, True)
        mock_strategy.check_market_book.side_effect = check_pattern
        self.flumine.add_strategy(mock_strategy)
        mock_market_book = mock.Mock(
            market_id="1.123", streaming_unique_id=1, runners=[]
        )
        mock_event = mock.Mock(event=[mock_market_book])
        process_call_count = 0
        for check_call_count, check_market_book_retval in enumerate(check_pattern, 1):
            self.flumine._process_market_books(mock_event)
            process_call_count += check_market_book_retval  # True == 1, False == 0
            self.assertEqual(
                mock_strategy.check_market_book.call_count, check_call_count
            )
            self.assertEqual(
                mock_strategy.process_market_book.call_count, process_call_count
            )

    def test_process_order_package(self):
        mock_order_package = mock.Mock()
        self.flumine.process_order_package(mock_order_package)
        self.assertEqual(self.flumine.handler_queue, [mock_order_package])

    def test__process_simulated_orders(self):
        mock_market = mock.Mock(context={})
        mock_market.blotter = Blotter("1.23")
        mock_order = mock.Mock(size_remaining=0, complete=False)
        mock_order.order_type.ORDER_TYPE = OrderTypes.LIMIT
        mock_order.trade.status = TradeStatus.COMPLETE
        mock_order_two = mock.Mock(size_remaining=1, complete=False)
        mock_order_two.order_type.ORDER_TYPE = OrderTypes.LIMIT
        mock_order_two.trade.status = TradeStatus.COMPLETE
        mock_market.blotter._live_orders = [mock_order, mock_order_two]
        self.flumine._process_simulated_orders(mock_market)
        mock_order.execution_complete.assert_called()
        mock_order_two.execution_complete.assert_not_called()

    def test__process_simulated_orders_strategies(self):
        mock_market = mock.Mock(context={})
        mock_market.blotter.live_orders = []
        mock_strategy = mock.Mock()
        self.flumine.strategies = [mock_strategy]
        self.flumine._process_simulated_orders(mock_market)
        mock_strategy.process_orders.assert_called_with(
            mock_market, mock_market.blotter.strategy_orders(mock_strategy)
        )

    def test__check_pending_packages_place(self):
        mock_client = mock.Mock()
        mock_order_package = mock.Mock(
            market_id="1.23",
            package_type=OrderPackageType.PLACE,
            elapsed_seconds=5,
            bet_delay=1,
            client=mock_client,
            simulated_delay=1.2,
        )
        self.flumine.handler_queue = [mock_order_package]
        self.flumine._check_pending_packages("1.23")
        mock_client.execution.handler.assert_called_with(mock_order_package)

    def test__check_pending_packages_place_pending(self):
        mock_client = mock.Mock()
        mock_order_package = mock.Mock(
            market_id="1.23",
            package_type=OrderPackageType.PLACE,
            elapsed_seconds=0.2,
            bet_delay=1,
            client=mock_client,
            simulated_delay=1.2,
        )
        self.flumine.handler_queue = [mock_order_package]
        self.flumine._check_pending_packages("1.23")
        mock_client.execution.handler.assert_not_called()

    def test__check_pending_packages_place_diff_market_id(self):
        mock_client = mock.Mock()
        mock_order_package = mock.Mock(
            market_id="1.23",
            package_type=OrderPackageType.PLACE,
            elapsed_seconds=2,
            bet_delay=1,
            client=mock_client,
            simulated_delay=1.2,
        )
        self.flumine.handler_queue = [mock_order_package]
        self.flumine._check_pending_packages("1.24")
        mock_client.execution.handler.assert_not_called()

    def test__check_pending_packages_cancel(self):
        mock_client = mock.Mock()
        mock_order_package = mock.Mock(
            market_id="1.23", elapsed_seconds=3, client=mock_client, simulated_delay=0.2
        )
        self.flumine.handler_queue = [mock_order_package]
        self.flumine._check_pending_packages("1.23")
        mock_client.execution.handler.assert_called_with(mock_order_package)

    def test__check_pending_packages_cancel_pending(self):
        mock_client = mock.Mock()
        mock_order_package = mock.Mock(
            market_id="1.23", elapsed_seconds=2, client=mock_client, simulated_delay=0.2
        )
        self.flumine.handler_queue = [mock_order_package]
        self.flumine._check_pending_packages("1.23")
        mock_client.execution.handler.assert_called_with(mock_order_package)

    def test__check_pending_packages_update(self):
        mock_client = mock.Mock()
        mock_order_package = mock.Mock(
            market_id="1.23", elapsed_seconds=3, client=mock_client, simulated_delay=0.2
        )
        self.flumine.handler_queue = [mock_order_package]
        self.flumine._check_pending_packages("1.23")
        mock_client.execution.handler.assert_called_with(mock_order_package)

    def test__check_pending_packages_update_pending(self):
        mock_client = mock.Mock()
        mock_order_package = mock.Mock(
            market_id="1.23", elapsed_seconds=2, client=mock_client, simulated_delay=0.2
        )
        self.flumine.handler_queue = [mock_order_package]
        self.flumine._check_pending_packages("1.23")
        mock_client.execution.handler.assert_called_with(mock_order_package)

    def test__check_pending_packages_replace(self):
        mock_client = mock.Mock()
        mock_order_package = mock.Mock(
            market_id="1.23",
            package_type=OrderPackageType.REPLACE,
            elapsed_seconds=5,
            bet_delay=1,
            client=mock_client,
            simulated_delay=1.2,
        )
        self.flumine.handler_queue = [mock_order_package]
        self.flumine._check_pending_packages("1.23")
        mock_client.execution.handler.assert_called_with(mock_order_package)

    def test__check_pending_packages_replace_pending(self):
        mock_client = mock.Mock()
        mock_order_package = mock.Mock(
            market_id="1.23",
            package_type=OrderPackageType.REPLACE,
            elapsed_seconds=2,
            bet_delay=1,
            client=mock_client,
            simulated_delay=1.2,
        )
        self.flumine.handler_queue.append(mock_order_package)
        self.flumine._check_pending_packages("1.23")
        mock_client.execution.handler.assert_called_with(mock_order_package)

    @mock.patch("flumine.baseflumine.BaseFlumine.info")
    @mock.patch("flumine.baseflumine.BaseFlumine.log_control")
    def test__process_close_market_closed(self, mock_log_control, mock_info):
        mock_strategy = mock.Mock()
        mock_strategy.stream_ids = [1, 2, 3]
        self.flumine.strategies = [mock_strategy]
        mock_market = mock.Mock(closed=False, elapsed_seconds_closed=None)
        mock_market.market_book.streaming_unique_id = 2
        mock_market.blotter.process_cleared_orders.return_value = []
        mock_market.cleared.return_value = {}
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
        assert str(self.flumine) == "<FlumineSimulation>"

    def test_repr(self):
        assert repr(self.flumine) == "<FlumineSimulation>"

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
