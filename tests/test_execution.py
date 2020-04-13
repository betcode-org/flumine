import unittest
from unittest import mock

from flumine.execution.baseexecution import BaseExecution, OrderPackageType
from flumine.execution.betfairexecution import BetfairExecution
from flumine.execution.simulatedexecution import SimulatedExecution
from flumine.clients.clients import ExchangeType


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


class SimulatedExecutionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_flumine = mock.Mock()
        self.execution = SimulatedExecution(self.mock_flumine)

    def test_init(self):
        self.assertEqual(self.execution.EXCHANGE, ExchangeType.BACKTEST)

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
