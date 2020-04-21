import unittest
from unittest import mock

from flumine.execution.baseexecution import BaseExecution, OrderPackageType
from flumine.execution.betfairexecution import BetfairExecution
from flumine.execution.simulatedexecution import SimulatedExecution
from flumine.clients.clients import ExchangeType
from flumine.exceptions import OrderExecutionError


class BaseExecutionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_flumine = mock.Mock()
        self.execution = BaseExecution(self.mock_flumine)

    def test_init(self):
        self.assertEqual(self.execution.flumine, self.mock_flumine)
        self.assertIsNotNone(self.execution._thread_pool)
        self.assertIsNone(self.execution.EXCHANGE)

    @mock.patch("flumine.execution.baseexecution.requests")
    @mock.patch("flumine.execution.baseexecution.BaseExecution.execute_place")
    def test_handler_place(self, mock_execute_place, mock_requests):
        mock_order_package = mock.Mock()
        mock_order_package.package_type = OrderPackageType.PLACE
        mock_thread_pool = mock.Mock()
        self.execution._thread_pool = mock_thread_pool
        self.execution.handler(mock_order_package)
        mock_thread_pool.submit.assert_called_with(
            mock_execute_place, mock_order_package, mock_requests.Session()
        )

    @mock.patch("flumine.execution.baseexecution.requests")
    @mock.patch("flumine.execution.baseexecution.BaseExecution.execute_cancel")
    def test_handler_cancel(self, mock_execute_cancel, mock_requests):
        mock_order_package = mock.Mock()
        mock_order_package.package_type = OrderPackageType.PLACE.CANCEL
        mock_thread_pool = mock.Mock()
        self.execution._thread_pool = mock_thread_pool
        self.execution.handler(mock_order_package)
        mock_thread_pool.submit.assert_called_with(
            mock_execute_cancel, mock_order_package, mock_requests.Session()
        )

    @mock.patch("flumine.execution.baseexecution.requests")
    @mock.patch("flumine.execution.baseexecution.BaseExecution.execute_replace")
    def test_handler_replace(self, mock_execute_replace, mock_requests):
        mock_order_package = mock.Mock()
        mock_order_package.package_type = OrderPackageType.REPLACE
        mock_thread_pool = mock.Mock()
        self.execution._thread_pool = mock_thread_pool
        self.execution.handler(mock_order_package)
        mock_thread_pool.submit.assert_called_with(
            mock_execute_replace, mock_order_package, mock_requests.Session()
        )

    @mock.patch("flumine.execution.baseexecution.requests")
    @mock.patch("flumine.execution.baseexecution.BaseExecution.execute_update")
    def test_handler_update(self, mock_execute_update, mock_requests):
        mock_order_package = mock.Mock()
        mock_order_package.package_type = OrderPackageType.UPDATE
        mock_thread_pool = mock.Mock()
        self.execution._thread_pool = mock_thread_pool
        self.execution.handler(mock_order_package)
        mock_thread_pool.submit.assert_called_with(
            mock_execute_update, mock_order_package, mock_requests.Session()
        )

    def test_handler_unknown(self):
        mock_order_package = mock.Mock()
        mock_order_package.package_type = "DELETE"
        with self.assertRaises(NotImplementedError):
            self.execution.handler(mock_order_package)

    def test_execute_place(self):
        with self.assertRaises(NotImplementedError):
            self.execution.execute_place(None, None)

    def test_execute_cancel(self):
        with self.assertRaises(NotImplementedError):
            self.execution.execute_place(None, None)

    def test_execute_update(self):
        with self.assertRaises(NotImplementedError):
            self.execution.execute_place(None, None)

    def test_execute_replace(self):
        with self.assertRaises(NotImplementedError):
            self.execution.execute_place(None, None)

    def test_handler_queue(self):
        self.assertEqual(self.execution.handler_queue, self.mock_flumine.handler_queue)

    def test_markets(self):
        self.assertEqual(self.execution.markets, self.mock_flumine.markets)


class BetfairExecutionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_flumine = mock.Mock()
        self.execution = BetfairExecution(self.mock_flumine)

    def test_init(self):
        self.assertEqual(self.execution.EXCHANGE, ExchangeType.BETFAIR)

    # @mock.patch("flumine.execution.betfairexecution.BetfairExecution.place")
    # @mock.patch("flumine.execution.betfairexecution.BetfairExecution._execution_helper")
    # def test_execute_place(self, mock__execution_helper, mock_place):
    #     mock_session = mock.Mock()
    #     mock_order_package = mock.Mock()
    #     mock_order_package.info = {}
    #     self.execution.execute_place(mock_order_package, mock_session)
    #     mock__execution_helper.assert_called_with(
    #         mock_place, mock_order_package, mock_session
    #     )

    def test_place(self):
        mock_session = mock.Mock()
        mock_order_package = mock.Mock()
        self.assertEqual(
            self.execution.place(mock_order_package, mock_session),
            mock_order_package.client.betting_client.betting.place_orders(),
        )

    @mock.patch("flumine.execution.betfairexecution.BetfairExecution.cancel")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._execution_helper")
    def test_execute_cancel(self, mock__execution_helper, mock_place):
        mock_session = mock.Mock()
        mock_order_package = mock.Mock()
        mock_order_package.info = {}
        self.execution.execute_cancel(mock_order_package, mock_session)
        mock__execution_helper.assert_called_with(
            mock_place, mock_order_package, mock_session
        )

    def test_cancel(self):
        mock_session = mock.Mock()
        mock_order_package = mock.Mock()
        mock_order_package.cancel_instructions = [1, 2]
        self.assertEqual(
            self.execution.cancel(mock_order_package, mock_session),
            mock_order_package.client.betting_client.betting.cancel_orders(),
        )

    def test_cancel_empty(self):
        mock_session = mock.Mock()
        mock_order_package = mock.Mock()
        mock_order_package.info = {}
        mock_order_package.cancel_instructions = []
        with self.assertRaises(OrderExecutionError):
            self.execution.cancel(mock_order_package, mock_session)

    def test_execute_update(self):
        with self.assertRaises(NotImplementedError):
            self.execution.execute_update(None, None)

    def test_execute_replace(self):
        with self.assertRaises(NotImplementedError):
            self.execution.execute_replace(None, None)

    def test__execution_helper(self):
        mock_trading_function = mock.Mock()
        mock_session = mock.Mock()
        mock_order_package = mock.Mock()
        self.execution._execution_helper(
            mock_trading_function, mock_order_package, mock_session
        )
        mock_trading_function.assert_called_with(mock_order_package, mock_session)

    def test__order_logger(self):
        mock_order = mock.Mock()
        mock_instruction_report = mock.Mock()
        self.execution._order_logger(
            mock_order, mock_instruction_report, OrderPackageType.PLACE
        )
        self.assertEqual(mock_order.bet_id, mock_instruction_report.bet_id)
        mock_order.responses.placed.assert_called_with(mock_instruction_report)

        self.execution._order_logger(
            mock_order, mock_instruction_report, OrderPackageType.CANCEL
        )
        mock_order.responses.cancelled.assert_called_with(mock_instruction_report)

        self.execution._order_logger(
            mock_order, mock_instruction_report, OrderPackageType.UPDATE
        )
        mock_order.responses.updated.assert_called_with(mock_instruction_report)

        self.execution._order_logger(
            mock_order, mock_instruction_report, OrderPackageType.REPLACE
        )
        self.assertEqual(mock_order.bet_id, mock_instruction_report.bet_id)
        mock_order.responses.replaced.assert_called_with(mock_instruction_report)

    def test__after_execution(self):
        mock_order = mock.Mock()
        self.execution._after_execution(mock_order)
        mock_order.executable.assert_called_with()


class SimulatedExecutionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_flumine = mock.Mock()
        self.execution = SimulatedExecution(self.mock_flumine)

    def test_init(self):
        self.assertEqual(self.execution.EXCHANGE, ExchangeType.SIMULATED)

    def test_execute_place(self):
        with self.assertRaises(NotImplementedError):
            self.execution.execute_place(None, None)

    def test_execute_cancel(self):
        with self.assertRaises(NotImplementedError):
            self.execution.execute_place(None, None)

    def test_execute_update(self):
        with self.assertRaises(NotImplementedError):
            self.execution.execute_place(None, None)

    def test_execute_replace(self):
        with self.assertRaises(NotImplementedError):
            self.execution.execute_place(None, None)
