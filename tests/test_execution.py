import time
import unittest
from unittest import mock
from unittest.mock import call

from betfairlightweight import BetfairError
from flumine.clients.clients import ExchangeType
from flumine.exceptions import OrderExecutionError
from flumine.execution.baseexecution import (
    MAX_WORKERS,
    MAX_SESSION_AGE,
    BET_ID_START,
    BaseExecution,
    OrderPackageType,
)
from flumine.execution.betfairexecution import BetfairExecution
from flumine.execution.simulatedexecution import SimulatedExecution


class BaseExecutionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_flumine = mock.Mock()
        self.execution = BaseExecution(self.mock_flumine, max_workers=2)

    def test_init(self):
        self.assertEqual(MAX_WORKERS, 32)
        self.assertEqual(MAX_SESSION_AGE, 200)
        self.assertEqual(BET_ID_START, 100000000000)
        self.assertEqual(self.execution.flumine, self.mock_flumine)
        self.assertEqual(self.execution._max_workers, 2)
        self.assertIsNotNone(self.execution._thread_pool)
        self.assertIsNone(self.execution.EXCHANGE)
        self.assertEqual(self.execution._bet_id, 100000000000)
        self.assertEqual(self.execution._sessions, [])
        self.assertEqual(self.execution._sessions_created, 0)

    @mock.patch("flumine.execution.baseexecution.BaseExecution._get_http_session")
    @mock.patch("flumine.execution.baseexecution.BaseExecution.execute_place")
    def test_handler_place(self, mock_execute_place, mock__get_http_session):
        mock_order_package = mock.Mock()
        mock_order_package.package_type = OrderPackageType.PLACE
        mock_thread_pool = mock.Mock()
        self.execution._thread_pool = mock_thread_pool
        self.execution.handler(mock_order_package)
        mock_thread_pool.submit.assert_called_with(
            mock_execute_place, mock_order_package, mock__get_http_session()
        )
        mock__get_http_session.assert_called_with()

    @mock.patch("flumine.execution.baseexecution.BaseExecution._get_http_session")
    @mock.patch("flumine.execution.baseexecution.BaseExecution.execute_cancel")
    def test_handler_cancel(self, mock_execute_cancel, mock__get_http_session):
        mock_order_package = mock.Mock()
        mock_order_package.package_type = OrderPackageType.PLACE.CANCEL
        mock_thread_pool = mock.Mock()
        self.execution._thread_pool = mock_thread_pool
        self.execution.handler(mock_order_package)
        mock_thread_pool.submit.assert_called_with(
            mock_execute_cancel, mock_order_package, mock__get_http_session()
        )
        mock__get_http_session.assert_called_with()

    @mock.patch("flumine.execution.baseexecution.BaseExecution._get_http_session")
    @mock.patch("flumine.execution.baseexecution.BaseExecution.execute_replace")
    def test_handler_replace(self, mock_execute_replace, mock__get_http_session):
        mock_order_package = mock.Mock()
        mock_order_package.package_type = OrderPackageType.REPLACE
        mock_thread_pool = mock.Mock()
        self.execution._thread_pool = mock_thread_pool
        self.execution.handler(mock_order_package)
        mock_thread_pool.submit.assert_called_with(
            mock_execute_replace, mock_order_package, mock__get_http_session()
        )
        mock__get_http_session.assert_called_with()

    @mock.patch("flumine.execution.baseexecution.BaseExecution._get_http_session")
    @mock.patch("flumine.execution.baseexecution.BaseExecution.execute_update")
    def test_handler_update(self, mock_execute_update, mock__get_http_session):
        mock_order_package = mock.Mock()
        mock_order_package.package_type = OrderPackageType.UPDATE
        mock_thread_pool = mock.Mock()
        self.execution._thread_pool = mock_thread_pool
        self.execution.handler(mock_order_package)
        mock_thread_pool.submit.assert_called_with(
            mock_execute_update, mock_order_package, mock__get_http_session()
        )
        mock__get_http_session.assert_called_with()

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

    @mock.patch("flumine.execution.baseexecution.BaseExecution._create_new_session")
    def test__get_http_session(self, mock__create_new_session):
        mock_session_one = mock.Mock(time_returned=time.time())
        mock_session_two = mock.Mock(time_returned=time.time())
        self.execution._sessions = [mock_session_one, mock_session_two]
        self.assertEqual(self.execution._get_http_session(), mock_session_two)
        self.assertEqual(self.execution._get_http_session(), mock_session_one)
        self.assertEqual(self.execution._get_http_session(), mock__create_new_session())

    @mock.patch("flumine.execution.baseexecution.BaseExecution._return_http_session")
    @mock.patch("flumine.execution.baseexecution.BaseExecution._create_new_session")
    def test__get_http_session_stale(
        self, mock__create_new_session, mock__return_http_session
    ):
        mock_session = mock.Mock(time_returned=123)
        self.execution._sessions = [mock_session]
        self.assertEqual(self.execution._get_http_session(), mock__create_new_session())
        mock__return_http_session.assert_called_with(mock_session, err=True)

    def test__create_new_session(self):
        session = self.execution._create_new_session()
        self.assertIsNotNone(session.time_created)
        self.assertIsNotNone(session.time_returned)

    def test__return_http_session(self):
        mock_session = mock.Mock()
        self.execution._return_http_session(mock_session)
        self.assertEqual(self.execution._sessions, [mock_session])
        self.execution._return_http_session(mock_session)
        self.execution._return_http_session(mock_session)
        self.assertEqual(self.execution._sessions, [mock_session, mock_session])
        self.assertGreater(mock_session.time_returned, 0)

    def test__return_http_session_close(self):
        self.execution._sessions = [1, 2]
        mock_session = mock.Mock()
        self.execution._return_http_session(mock_session)
        mock_session.close.assert_called_with()

    def test__return_http_session_err_close(self):
        mock_session = mock.Mock()
        self.execution._return_http_session(mock_session, err=True)
        mock_session.close.assert_called_with()

    @mock.patch("flumine.execution.baseexecution.OrderEvent")
    def test__order_logger_place(self, mock_order_event):
        mock_order = mock.Mock()
        mock_instruction_report = mock.Mock()
        self.execution._order_logger(
            mock_order, mock_instruction_report, OrderPackageType.PLACE
        )
        self.assertEqual(mock_order.bet_id, mock_instruction_report.bet_id)
        mock_order.responses.placed.assert_called_with(mock_instruction_report)
        self.mock_flumine.log_control.assert_called_with(mock_order_event(mock_order))

    def test__order_logger_cancel(self):
        mock_order = mock.Mock()
        mock_instruction_report = mock.Mock()
        self.execution._order_logger(
            mock_order, mock_instruction_report, OrderPackageType.CANCEL
        )
        mock_order.responses.cancelled.assert_called_with(mock_instruction_report)

    def test__order_logger_update(self):
        mock_order = mock.Mock()
        mock_instruction_report = mock.Mock()
        self.execution._order_logger(
            mock_order, mock_instruction_report, OrderPackageType.UPDATE
        )
        mock_order.responses.updated.assert_called_with(mock_instruction_report)

    @mock.patch("flumine.execution.baseexecution.OrderEvent")
    def test__order_logger_replace(self, mock_order_event):
        mock_order = mock.Mock()
        mock_instruction_report = mock.Mock()
        self.execution._order_logger(
            mock_order, mock_instruction_report, OrderPackageType.REPLACE
        )
        self.assertEqual(mock_order.bet_id, mock_instruction_report.bet_id)
        mock_order.responses.placed.assert_called_with(mock_instruction_report)
        self.mock_flumine.log_control.assert_called_with(mock_order_event(mock_order))

    def test_shutdown(self):
        self.execution.shutdown()
        self.assertTrue(self.execution._thread_pool._shutdown)


class BetfairExecutionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_flumine = mock.Mock()
        self.execution = BetfairExecution(self.mock_flumine)

    def test_init(self):
        self.assertEqual(self.execution.EXCHANGE, ExchangeType.BETFAIR)

    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._order_logger")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution.place")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._execution_helper")
    def test_execute_place_success(
        self, mock__execution_helper, mock_place, mock__order_logger
    ):
        mock_session = mock.Mock()
        mock_order = mock.Mock()
        mock_order.trade.__enter__ = mock.Mock()
        mock_order.trade.__exit__ = mock.Mock()
        mock_order_package = mock.Mock()
        mock_order_package.__iter__ = mock.Mock(return_value=iter([mock_order]))
        mock_order_package.info = {}
        mock_report = mock.Mock()
        mock_instruction_report = mock.Mock()
        mock_instruction_report.status = "SUCCESS"
        mock_report.place_instruction_reports = [mock_instruction_report]
        mock__execution_helper.return_value = mock_report
        self.execution.execute_place(mock_order_package, mock_session)
        mock__execution_helper.assert_called_with(
            mock_place, mock_order_package, mock_session
        )
        mock__order_logger.assert_called_with(
            mock_order, mock_instruction_report, OrderPackageType.PLACE
        )
        mock_order.executable.assert_called_with()
        mock_order.trade.__enter__.assert_called_with()
        mock_order.trade.__exit__.assert_called_with(None, None, None)

    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._order_logger")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution.place")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._execution_helper")
    def test_execute_place_failure(
        self, mock__execution_helper, mock_place, mock__order_logger
    ):
        mock_session = mock.Mock()
        mock_order = mock.Mock()
        mock_order.trade.__enter__ = mock.Mock()
        mock_order.trade.__exit__ = mock.Mock()
        mock_order_package = mock.Mock()
        mock_order_package.__iter__ = mock.Mock(return_value=iter([mock_order]))
        mock_order_package.info = {}
        mock_report = mock.Mock()
        mock_instruction_report = mock.Mock()
        mock_instruction_report.status = "FAILURE"
        mock_report.place_instruction_reports = [mock_instruction_report]
        mock__execution_helper.return_value = mock_report
        self.execution.execute_place(mock_order_package, mock_session)
        mock__execution_helper.assert_called_with(
            mock_place, mock_order_package, mock_session
        )
        mock__order_logger.assert_called_with(
            mock_order, mock_instruction_report, OrderPackageType.PLACE
        )
        mock_order.lapsed.assert_called_with()
        mock_order.trade.__enter__.assert_called_with()
        mock_order.trade.__exit__.assert_called_with(None, None, None)

    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._order_logger")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution.place")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._execution_helper")
    def test_execute_place_timeout(
        self, mock__execution_helper, mock_place, mock__order_logger
    ):
        mock_session = mock.Mock()
        mock_order = mock.Mock()
        mock_order.trade.__enter__ = mock.Mock()
        mock_order.trade.__exit__ = mock.Mock()
        mock_order_package = mock.Mock()
        mock_order_package.__iter__ = mock.Mock(return_value=iter([mock_order]))
        mock_order_package.info = {}
        mock_report = mock.Mock()
        mock_instruction_report = mock.Mock()
        mock_instruction_report.status = "TIMEOUT"
        mock_report.place_instruction_reports = [mock_instruction_report]
        mock__execution_helper.return_value = mock_report
        self.execution.execute_place(mock_order_package, mock_session)
        mock__execution_helper.assert_called_with(
            mock_place, mock_order_package, mock_session
        )
        mock__order_logger.assert_called_with(
            mock_order, mock_instruction_report, OrderPackageType.PLACE
        )
        # mock_order.lapsed.assert_called_with()
        mock_order.trade.__enter__.assert_called_with()
        mock_order.trade.__exit__.assert_called_with(None, None, None)

    @mock.patch("flumine.execution.betfairexecution.BetfairExecution.place")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._execution_helper")
    def test_execute_place_error(self, mock__execution_helper, mock_place):
        mock_session = mock.Mock()
        mock_order_package = mock.Mock()
        mock_order_package.info = {}
        mock__execution_helper.return_value = None
        self.execution.execute_place(mock_order_package, mock_session)
        mock__execution_helper.assert_called_with(
            mock_place, mock_order_package, mock_session
        )

    def test_place(self):
        mock_session = mock.Mock()
        mock_order_package = mock.Mock()
        self.assertEqual(
            self.execution.place(mock_order_package, mock_session),
            mock_order_package.client.betting_client.betting.place_orders(),
        )

    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._order_logger")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution.cancel")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._execution_helper")
    def test_execute_cancel_success(
        self, mock__execution_helper, mock_cancel, mock__order_logger
    ):
        mock_session = mock.Mock()
        mock_order = mock.Mock()
        mock_order.trade.__enter__ = mock.Mock()
        mock_order.trade.__exit__ = mock.Mock()
        mock_order.bet_id = 123
        mock_order.size_remaining = 2
        mock_order_package = mock.Mock()
        mock_order_package.__iter__ = mock.Mock(return_value=iter([mock_order]))
        mock_order_package.info = {}
        mock_report = mock.Mock()
        mock_instruction_report = mock.Mock()
        mock_instruction_report.status = "SUCCESS"
        mock_instruction_report.instruction.bet_id = 123
        mock_instruction_report.size_cancelled = 2
        mock_report.cancel_instruction_reports = [mock_instruction_report]
        mock__execution_helper.return_value = mock_report
        self.execution.execute_cancel(mock_order_package, mock_session)
        mock__execution_helper.assert_called_with(
            mock_cancel, mock_order_package, mock_session
        )
        mock__order_logger.assert_called_with(
            mock_order, mock_instruction_report, OrderPackageType.CANCEL
        )
        mock_order.execution_complete.assert_called_with()
        mock_order.trade.__enter__.assert_called_with()
        mock_order.trade.__exit__.assert_called_with(None, None, None)

    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._order_logger")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution.cancel")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._execution_helper")
    def test_execute_cancel_success_partial(
        self, mock__execution_helper, mock_cancel, mock__order_logger
    ):
        mock_session = mock.Mock()
        mock_order = mock.Mock()
        mock_order.trade.__enter__ = mock.Mock()
        mock_order.trade.__exit__ = mock.Mock()
        mock_order.bet_id = 123
        mock_order.size_remaining = 2
        mock_order_package = mock.Mock()
        mock_order_package.__iter__ = mock.Mock(return_value=iter([mock_order]))
        mock_order_package.info = {}
        mock_report = mock.Mock()
        mock_instruction_report = mock.Mock()
        mock_instruction_report.status = "SUCCESS"
        mock_instruction_report.instruction.bet_id = 123
        mock_instruction_report.size_cancelled = 1
        mock_report.cancel_instruction_reports = [mock_instruction_report]
        mock__execution_helper.return_value = mock_report
        self.execution.execute_cancel(mock_order_package, mock_session)
        mock__execution_helper.assert_called_with(
            mock_cancel, mock_order_package, mock_session
        )
        mock__order_logger.assert_called_with(
            mock_order, mock_instruction_report, OrderPackageType.CANCEL
        )
        mock_order.executable.assert_called_with()
        mock_order.trade.__enter__.assert_called_with()
        mock_order.trade.__exit__.assert_called_with(None, None, None)

    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._order_logger")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution.cancel")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._execution_helper")
    def test_execute_cancel_failure(
        self, mock__execution_helper, mock_cancel, mock__order_logger
    ):
        mock_session = mock.Mock()
        mock_order = mock.Mock()
        mock_order.trade.__enter__ = mock.Mock()
        mock_order.trade.__exit__ = mock.Mock()
        mock_order.bet_id = 123
        mock_order_package = mock.Mock()
        mock_order_package.__iter__ = mock.Mock(return_value=iter([mock_order]))
        mock_order_package.info = {}
        mock_report = mock.Mock()
        mock_instruction_report = mock.Mock()
        mock_instruction_report.status = "FAILURE"
        mock_instruction_report.instruction.bet_id = 123
        mock_report.cancel_instruction_reports = [mock_instruction_report]
        mock__execution_helper.return_value = mock_report
        self.execution.execute_cancel(mock_order_package, mock_session)
        mock__execution_helper.assert_called_with(
            mock_cancel, mock_order_package, mock_session
        )
        mock__order_logger.assert_called_with(
            mock_order, mock_instruction_report, OrderPackageType.CANCEL
        )
        mock_order.executable.assert_called_with()
        mock_order.trade.__enter__.assert_called_with()
        mock_order.trade.__exit__.assert_called_with(None, None, None)

    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._order_logger")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution.cancel")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._execution_helper")
    def test_execute_cancel_timeout(
        self, mock__execution_helper, mock_cancel, mock__order_logger
    ):
        mock_session = mock.Mock()
        mock_order = mock.Mock()
        mock_order.trade.__enter__ = mock.Mock()
        mock_order.trade.__exit__ = mock.Mock()
        mock_order.bet_id = 123
        mock_order_package = mock.Mock()
        mock_order_package.__iter__ = mock.Mock(return_value=iter([mock_order]))
        mock_order_package.info = {}
        mock_report = mock.Mock()
        mock_instruction_report = mock.Mock()
        mock_instruction_report.status = "TIMEOUT"
        mock_instruction_report.instruction.bet_id = 123
        mock_report.cancel_instruction_reports = [mock_instruction_report]
        mock__execution_helper.return_value = mock_report
        self.execution.execute_cancel(mock_order_package, mock_session)
        mock__execution_helper.assert_called_with(
            mock_cancel, mock_order_package, mock_session
        )
        mock__order_logger.assert_called_with(
            mock_order, mock_instruction_report, OrderPackageType.CANCEL
        )
        mock_order.executable.assert_called_with()
        mock_order.trade.__enter__.assert_called_with()
        mock_order.trade.__exit__.assert_called_with(None, None, None)

    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._order_logger")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution.cancel")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._execution_helper")
    def test_execute_cancel_not_returned(
        self, mock__execution_helper, mock_cancel, mock__order_logger
    ):
        mock_session = mock.Mock()
        mock_order = mock.Mock()
        mock_order.trade.__enter__ = mock.Mock()
        mock_order.trade.__exit__ = mock.Mock()
        mock_order.bet_id = 123
        mock_order_package = mock.Mock()
        mock_order_package.__iter__ = mock.Mock(return_value=iter([mock_order]))
        mock_order_package.info = {}
        mock_report = mock.Mock()
        mock_report.cancel_instruction_reports = []
        mock__execution_helper.return_value = mock_report
        self.execution.execute_cancel(mock_order_package, mock_session)
        mock__execution_helper.assert_called_with(
            mock_cancel, mock_order_package, mock_session
        )
        mock_order.executable.assert_called_with()
        mock_order.trade.__enter__.assert_called_with()
        mock_order.trade.__exit__.assert_called_with(None, None, None)

    @mock.patch("flumine.execution.betfairexecution.BetfairExecution.cancel")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._execution_helper")
    def test_execute_cancel_error(self, mock__execution_helper, mock_place):
        mock_session = mock.Mock()
        mock_order_package = mock.Mock()
        mock_order_package.info = {}
        mock__execution_helper.return_value = None
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

    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._order_logger")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution.update")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._execution_helper")
    def test_execute_update_success(
        self, mock__execution_helper, mock_update, mock__order_logger
    ):
        mock_session = mock.Mock()
        mock_order = mock.Mock()
        mock_order.trade.__enter__ = mock.Mock()
        mock_order.trade.__exit__ = mock.Mock()
        mock_order.bet_id = 123
        mock_order_package = mock.Mock()
        mock_order_package.__iter__ = mock.Mock(return_value=iter([mock_order]))
        mock_order_package.info = {}
        mock_report = mock.Mock()
        mock_instruction_report = mock.Mock()
        mock_instruction_report.status = "SUCCESS"
        mock_report.update_instruction_reports = [mock_instruction_report]
        mock__execution_helper.return_value = mock_report
        self.execution.execute_update(mock_order_package, mock_session)
        mock__execution_helper.assert_called_with(
            mock_update, mock_order_package, mock_session
        )
        mock__order_logger.assert_called_with(
            mock_order, mock_instruction_report, OrderPackageType.UPDATE
        )
        mock_order.executable.assert_called_with()
        mock_order.trade.__enter__.assert_called_with()
        mock_order.trade.__exit__.assert_called_with(None, None, None)

    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._order_logger")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution.update")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._execution_helper")
    def test_execute_update_failure(
        self, mock__execution_helper, mock_update, mock__order_logger
    ):
        mock_session = mock.Mock()
        mock_order = mock.Mock()
        mock_order.trade.__enter__ = mock.Mock()
        mock_order.trade.__exit__ = mock.Mock()
        mock_order.bet_id = 123
        mock_order_package = mock.Mock()
        mock_order_package.__iter__ = mock.Mock(return_value=iter([mock_order]))
        mock_order_package.info = {}
        mock_report = mock.Mock()
        mock_instruction_report = mock.Mock()
        mock_instruction_report.status = "FAILURE"
        mock_report.update_instruction_reports = [mock_instruction_report]
        mock__execution_helper.return_value = mock_report
        self.execution.execute_update(mock_order_package, mock_session)
        mock__execution_helper.assert_called_with(
            mock_update, mock_order_package, mock_session
        )
        mock__order_logger.assert_called_with(
            mock_order, mock_instruction_report, OrderPackageType.UPDATE
        )
        mock_order.executable.assert_called_with()
        mock_order.trade.__enter__.assert_called_with()
        mock_order.trade.__exit__.assert_called_with(None, None, None)

    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._order_logger")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution.update")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._execution_helper")
    def test_execute_update_timeout(
        self, mock__execution_helper, mock_update, mock__order_logger
    ):
        mock_session = mock.Mock()
        mock_order = mock.Mock()
        mock_order.trade.__enter__ = mock.Mock()
        mock_order.trade.__exit__ = mock.Mock()
        mock_order.bet_id = 123
        mock_order_package = mock.Mock()
        mock_order_package.__iter__ = mock.Mock(return_value=iter([mock_order]))
        mock_order_package.info = {}
        mock_report = mock.Mock()
        mock_instruction_report = mock.Mock()
        mock_instruction_report.status = "TIMEOUT"
        mock_report.update_instruction_reports = [mock_instruction_report]
        mock__execution_helper.return_value = mock_report
        self.execution.execute_update(mock_order_package, mock_session)
        mock__execution_helper.assert_called_with(
            mock_update, mock_order_package, mock_session
        )
        mock__order_logger.assert_called_with(
            mock_order, mock_instruction_report, OrderPackageType.UPDATE
        )
        mock_order.executable.assert_called_with()
        mock_order.trade.__enter__.assert_called_with()
        mock_order.trade.__exit__.assert_called_with(None, None, None)

    @mock.patch("flumine.execution.betfairexecution.BetfairExecution.update")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._execution_helper")
    def test_execute_update_error(self, mock__execution_helper, mock_update):
        mock_session = mock.Mock()
        mock_order_package = mock.Mock()
        mock_order_package.info = {}
        mock__execution_helper.return_value = None
        self.execution.execute_update(mock_order_package, mock_session)
        mock__execution_helper.assert_called_with(
            mock_update, mock_order_package, mock_session
        )

    def test_update(self):
        mock_session = mock.Mock()
        mock_order_package = mock.Mock()
        self.assertEqual(
            self.execution.update(mock_order_package, mock_session),
            mock_order_package.client.betting_client.betting.update_orders(),
        )

    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._order_logger")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution.replace")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._execution_helper")
    def test_execute_replace_success(
        self, mock__execution_helper, mock_replace, mock__order_logger
    ):
        mock_market = mock.Mock()
        self.mock_flumine.markets.markets = {"1.23": mock_market}
        mock_session = mock.Mock()
        mock_order = mock.Mock(market_id="1.23", bet_id=123)
        mock_order.trade.__enter__ = mock.Mock()
        mock_order.trade.__exit__ = mock.Mock()
        mock_order_package = mock.Mock(market_id="1.23", info={})
        mock_order_package.__iter__ = mock.Mock(return_value=iter([mock_order]))
        mock_report = mock.Mock()
        mock_instruction_report = mock.Mock()
        mock_instruction_report.cancel_instruction_reports.status = "SUCCESS"
        mock_instruction_report.place_instruction_reports.status = "SUCCESS"
        mock_report.replace_instruction_reports = [mock_instruction_report]
        mock__execution_helper.return_value = mock_report
        self.execution.execute_replace(mock_order_package, mock_session)
        mock__execution_helper.assert_called_with(
            mock_replace, mock_order_package, mock_session
        )
        # mock__order_logger.assert_called_with(
        #     mock_order, mock_instruction_report, OrderPackageType.CANCEL
        # )
        mock_order.execution_complete.assert_called_with()
        replacement_order = mock_order.trade.create_order_replacement()
        replacement_order.executable.assert_called_with()
        mock_market.place_order.assert_called_with(replacement_order, execute=False)
        mock__order_logger.assert_called_with(
            replacement_order,
            mock_instruction_report.place_instruction_reports,
            OrderPackageType.REPLACE,
        )
        mock_order.trade.__enter__.assert_called_with()
        mock_order.trade.__exit__.assert_called_with(None, None, None)

    @mock.patch("flumine.execution.betfairexecution.BetfairExecution.replace")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._execution_helper")
    def test_execute_replace_error(self, mock__execution_helper, mock_replace):
        mock_session = mock.Mock()
        mock_order_package = mock.Mock()
        mock_order_package.info = {}
        mock__execution_helper.return_value = None
        self.execution.execute_replace(mock_order_package, mock_session)
        mock__execution_helper.assert_called_with(
            mock_replace, mock_order_package, mock_session
        )

    def test_replace(self):
        mock_session = mock.Mock()
        mock_order_package = mock.Mock()
        self.assertEqual(
            self.execution.replace(mock_order_package, mock_session),
            mock_order_package.client.betting_client.betting.replace_orders(),
        )

    @mock.patch(
        "flumine.execution.betfairexecution.BetfairExecution._return_http_session"
    )
    def test__execution_helper(self, mock__return_http_session):
        mock_trading_function = mock.Mock()
        mock_trading_function.__name__ = "test"
        mock_session = mock.Mock()
        mock_order_package = mock.Mock()
        mock_order_package.info = {}
        self.execution._execution_helper(
            mock_trading_function, mock_order_package, mock_session
        )
        mock_trading_function.assert_called_with(mock_order_package, mock_session)
        mock__return_http_session.assert_called_with(mock_session)

    @mock.patch(
        "flumine.execution.betfairexecution.BetfairExecution._return_http_session"
    )
    def test__execution_helper_empty(self, mock__return_http_session):
        mock_trading_function = mock.Mock()
        mock_trading_function.__name__ = "test"
        mock_session = mock.Mock()
        mock_order_package = mock.Mock(orders=[])
        mock_order_package.info = {}
        self.execution._execution_helper(
            mock_trading_function, mock_order_package, mock_session
        )
        mock_trading_function.assert_not_called()
        mock__return_http_session.assert_called_with(mock_session)

    @mock.patch("flumine.execution.betfairexecution.BetfairExecution.handler")
    @mock.patch(
        "flumine.execution.betfairexecution.BetfairExecution._return_http_session"
    )
    def test__execution_helper_error(self, mock__return_http_session, mock_handler):
        mock_trading_function = mock.Mock()
        mock_trading_function.__name__ = "test"
        mock_trading_function.side_effect = BetfairError()
        mock_session = mock.Mock()
        mock_order_package = mock.Mock()
        mock_order_package.info = {}
        mock_order_package.retry.return_value = True
        self.assertIsNone(
            self.execution._execution_helper(
                mock_trading_function, mock_order_package, mock_session
            )
        )
        mock_trading_function.assert_called_with(mock_order_package, mock_session)
        mock__return_http_session.assert_called_with(mock_session, err=True)
        mock_handler.assert_called_with(mock_order_package)

    @mock.patch("flumine.execution.betfairexecution.BetfairExecution.handler")
    @mock.patch(
        "flumine.execution.betfairexecution.BetfairExecution._return_http_session"
    )
    def test__execution_helper_error_no_retry(
        self, mock__return_http_session, mock_handler
    ):
        mock_trading_function = mock.Mock()
        mock_trading_function.__name__ = "test"
        mock_trading_function.side_effect = BetfairError()
        mock_session = mock.Mock()
        mock_order_package = mock.Mock()
        mock_order_package.info = {}
        mock_order_package.retry.return_value = False
        self.assertIsNone(
            self.execution._execution_helper(
                mock_trading_function, mock_order_package, mock_session
            )
        )
        mock_trading_function.assert_called_with(mock_order_package, mock_session)
        mock__return_http_session.assert_called_with(mock_session, err=True)
        mock_handler.put.assert_not_called()

    @mock.patch(
        "flumine.execution.betfairexecution.BetfairExecution._return_http_session"
    )
    def test__execution_helper_unknown_error(self, mock__return_http_session):
        mock_trading_function = mock.Mock()
        mock_trading_function.__name__ = "test"
        mock_trading_function.side_effect = ValueError()
        mock_session = mock.Mock()
        mock_order_package = mock.Mock()
        mock_order_package.info = {}
        mock_order_package.retry.return_value = True
        self.assertIsNone(
            self.execution._execution_helper(
                mock_trading_function, mock_order_package, mock_session
            )
        )
        mock_trading_function.assert_called_with(mock_order_package, mock_session)
        mock__return_http_session.assert_called_with(mock_session, err=True)


class SimulatedExecutionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_market = mock.Mock()
        self.mock_flumine = mock.Mock()
        self.mock_flumine.markets.markets = {"1.23": self.mock_market}
        self.execution = SimulatedExecution(self.mock_flumine)

    def test_init(self):
        self.assertEqual(self.execution.EXCHANGE, ExchangeType.SIMULATED)

    @mock.patch("flumine.execution.simulatedexecution.SimulatedExecution.execute_place")
    def test_handler_paper_trade(self, mock_execute_place):
        mock_thread_pool = mock.Mock()
        self.execution._thread_pool = mock_thread_pool
        mock_order_package = mock.Mock()
        mock_order_package.client.paper_trade = True
        mock_order_package.package_type = OrderPackageType.PLACE
        self.execution.handler(mock_order_package)
        mock_thread_pool.submit.assert_called_with(
            mock_execute_place, mock_order_package, None
        )

    @mock.patch("flumine.execution.simulatedexecution.SimulatedExecution.execute_place")
    def test_handler_place(self, mock_execute_place):
        mock_order_package = mock.Mock()
        mock_order_package.client.paper_trade = False
        mock_order_package.package_type = OrderPackageType.PLACE
        self.execution.handler(mock_order_package)
        mock_execute_place.assert_called_with(mock_order_package, http_session=None)

    @mock.patch(
        "flumine.execution.simulatedexecution.SimulatedExecution.execute_cancel"
    )
    def test_handler_cancel(self, mock_execute_cancel):
        mock_order_package = mock.Mock()
        mock_order_package.client.paper_trade = False
        mock_order_package.package_type = OrderPackageType.PLACE.CANCEL
        self.execution.handler(mock_order_package)
        mock_execute_cancel.assert_called_with(mock_order_package, http_session=None)

    @mock.patch(
        "flumine.execution.simulatedexecution.SimulatedExecution.execute_update"
    )
    def test_handler_update(self, mock_execute_update):
        mock_order_package = mock.Mock()
        mock_order_package.client.paper_trade = False
        mock_order_package.package_type = OrderPackageType.UPDATE
        self.execution.handler(mock_order_package)
        mock_execute_update.assert_called_with(mock_order_package, http_session=None)

    @mock.patch(
        "flumine.execution.simulatedexecution.SimulatedExecution.execute_replace"
    )
    def test_handler_replace(self, mock_execute_replace):
        mock_order_package = mock.Mock()
        mock_order_package.client.paper_trade = False
        mock_order_package.package_type = OrderPackageType.REPLACE
        self.execution.handler(mock_order_package)
        mock_execute_replace.assert_called_with(mock_order_package, http_session=None)

    @mock.patch("flumine.execution.simulatedexecution.SimulatedExecution._order_logger")
    def test_execute_place_success(self, mock__order_logger):
        mock_order = mock.Mock()
        mock_order.trade.__enter__ = mock.Mock()
        mock_order.trade.__exit__ = mock.Mock()
        mock_order_package = mock.Mock(market_id="1.23")
        mock_order_package.client.paper_trade = False
        mock_order_package.__iter__ = mock.Mock(return_value=iter([mock_order]))
        mock_order_package.place_instructions = [1]
        mock_order_package.info = {}
        mock_sim_resp = mock.Mock()
        mock_sim_resp.status = "SUCCESS"
        mock_order.simulated.place.return_value = mock_sim_resp
        self.execution.execute_place(mock_order_package, None)
        mock_order.simulated.place.assert_called_with(
            mock_order_package.client,
            self.mock_market.market_book,
            1,
            self.execution._bet_id,
        )
        mock__order_logger.assert_called_with(
            mock_order, mock_sim_resp, mock_order_package.package_type
        )
        mock_order.executable.assert_called_with()
        mock_order.trade.__enter__.assert_called_with()
        mock_order.trade.__exit__.assert_called_with(None, None, None)

    @mock.patch("flumine.execution.simulatedexecution.SimulatedExecution._order_logger")
    def test_execute_place_failure(self, mock__order_logger):
        mock_order = mock.Mock()
        mock_order.trade.__enter__ = mock.Mock()
        mock_order.trade.__exit__ = mock.Mock()
        mock_order_package = mock.Mock(market_id="1.23")
        mock_order_package.client.paper_trade = False
        mock_order_package.__iter__ = mock.Mock(return_value=iter([mock_order]))
        mock_order_package.place_instructions = [1]
        mock_order_package.info = {}
        mock_sim_resp = mock.Mock()
        mock_sim_resp.status = "FAILURE"
        mock_order.simulated.place.return_value = mock_sim_resp
        self.execution.execute_place(mock_order_package, None)
        mock_order.simulated.place.assert_called_with(
            mock_order_package.client,
            self.mock_market.market_book,
            1,
            self.execution._bet_id,
        )
        mock__order_logger.assert_called_with(
            mock_order, mock_sim_resp, mock_order_package.package_type
        )
        mock_order.lapsed.assert_called_with()
        mock_order.trade.__enter__.assert_called_with()
        mock_order.trade.__exit__.assert_called_with(None, None, None)

    @mock.patch("flumine.execution.simulatedexecution.time")
    def test_execute_place_paper_trade(self, mock_time):
        mock_order_package = mock.Mock(
            market_id="1.23", place_instructions=[], bet_delay=1
        )
        mock_order_package.__iter__ = mock.Mock(return_value=iter([]))
        mock_order_package.client.paper_trade = True
        self.execution.execute_place(mock_order_package, None)
        mock_time.sleep.assert_called_with(self.execution.PLACE_LATENCY + 1)

    @mock.patch("flumine.execution.simulatedexecution.SimulatedExecution._order_logger")
    def test_execute_cancel(self, mock__order_logger):
        mock_order = mock.Mock(size_cancelled=2, size_remaining=0)
        mock_order.trade.__enter__ = mock.Mock()
        mock_order.trade.__exit__ = mock.Mock()
        mock_order_package = mock.Mock()
        mock_order_package.client.paper_trade = False
        mock_order_package.__iter__ = mock.Mock(return_value=iter([mock_order]))
        mock_sim_resp = mock.Mock()
        mock_sim_resp.status = "SUCCESS"
        mock_order.simulated.cancel.return_value = mock_sim_resp
        self.execution.execute_cancel(mock_order_package, None)
        mock_order.simulated.cancel.assert_called_with()
        mock__order_logger.assert_called_with(
            mock_order, mock_sim_resp, mock_order_package.package_type
        )
        mock_order.execution_complete.assert_called_with()
        mock_order.trade.__enter__.assert_called_with()
        mock_order.trade.__exit__.assert_called_with(None, None, None)

    @mock.patch("flumine.execution.simulatedexecution.SimulatedExecution._order_logger")
    def test_execute_cancel_executable(self, mock__order_logger):
        mock_order = mock.Mock(size_cancelled=2, size_remaining=2)
        mock_order.trade.__enter__ = mock.Mock()
        mock_order.trade.__exit__ = mock.Mock()
        mock_order_package = mock.Mock()
        mock_order_package.client.paper_trade = False
        mock_order_package.__iter__ = mock.Mock(return_value=iter([mock_order]))
        mock_sim_resp = mock.Mock()
        mock_sim_resp.status = "SUCCESS"
        mock_order.simulated.cancel.return_value = mock_sim_resp
        self.execution.execute_cancel(mock_order_package, None)
        mock_order.simulated.cancel.assert_called_with()
        mock__order_logger.assert_called_with(
            mock_order, mock_sim_resp, mock_order_package.package_type
        )
        mock_order.executable.assert_called_with()
        mock_order.trade.__enter__.assert_called_with()
        mock_order.trade.__exit__.assert_called_with(None, None, None)

    @mock.patch("flumine.execution.simulatedexecution.SimulatedExecution._order_logger")
    def test_execute_cancel_failure(self, mock__order_logger):
        mock_order = mock.Mock()
        mock_order.trade.__enter__ = mock.Mock()
        mock_order.trade.__exit__ = mock.Mock()
        mock_order_package = mock.Mock()
        mock_order_package.client.paper_trade = False
        mock_order_package.__iter__ = mock.Mock(return_value=iter([mock_order]))
        mock_sim_resp = mock.Mock()
        mock_sim_resp.status = "FAILURE"
        mock_order.simulated.cancel.return_value = mock_sim_resp
        self.execution.execute_cancel(mock_order_package, None)
        mock_order.simulated.cancel.assert_called_with()
        mock__order_logger.assert_called_with(
            mock_order, mock_sim_resp, mock_order_package.package_type
        )
        mock_order.executable.assert_called_with()
        mock_order.trade.__enter__.assert_called_with()
        mock_order.trade.__exit__.assert_called_with(None, None, None)

    @mock.patch("flumine.execution.simulatedexecution.time")
    def test_execute_cancel_paper_trade(self, mock_time):
        mock_order_package = mock.Mock(bet_delay=1)
        mock_order_package.__iter__ = mock.Mock(return_value=iter([]))
        mock_order_package.client.paper_trade = True
        self.execution.execute_cancel(mock_order_package, None)
        mock_time.sleep.assert_called_with(self.execution.CANCEL_LATENCY)

    @mock.patch("flumine.execution.simulatedexecution.SimulatedExecution._order_logger")
    def test_execute_update(self, mock__order_logger):
        mock_order = mock.Mock()
        mock_order.trade.__enter__ = mock.Mock()
        mock_order.trade.__exit__ = mock.Mock()
        mock_order_package = mock.Mock()
        mock_order_package.client.paper_trade = False
        mock_order_package.__iter__ = mock.Mock(return_value=iter([mock_order]))
        mock_order_package.update_instructions = ["PERSIST"]
        mock_order_package.info = {}
        mock_sim_resp = mock.Mock()
        mock_sim_resp.status = "SUCCESS"
        mock_order.simulated.update.return_value = mock_sim_resp
        self.execution.execute_update(mock_order_package, None)
        mock_order.simulated.update.assert_called_with("PERSIST")
        mock__order_logger.assert_called_with(
            mock_order, mock_sim_resp, mock_order_package.package_type
        )
        mock_order.executable.assert_called_with()
        mock_order.trade.__enter__.assert_called_with()
        mock_order.trade.__exit__.assert_called_with(None, None, None)

    @mock.patch("flumine.execution.simulatedexecution.SimulatedExecution._order_logger")
    def test_execute_update_failure(self, mock__order_logger):
        mock_order = mock.Mock()
        mock_order.trade.__enter__ = mock.Mock()
        mock_order.trade.__exit__ = mock.Mock()
        mock_order_package = mock.Mock()
        mock_order_package.client.paper_trade = False
        mock_order_package.__iter__ = mock.Mock(return_value=iter([mock_order]))
        mock_order_package.update_instructions = ["PERSIST"]
        mock_order_package.info = {}
        mock_sim_resp = mock.Mock()
        mock_sim_resp.status = "FAILURE"
        mock_order.simulated.update.return_value = mock_sim_resp
        self.execution.execute_update(mock_order_package, None)
        mock_order.simulated.update.assert_called_with("PERSIST")
        mock__order_logger.assert_called_with(
            mock_order, mock_sim_resp, mock_order_package.package_type
        )
        mock_order.executable.assert_called_with()
        mock_order.trade.__enter__.assert_called_with()
        mock_order.trade.__exit__.assert_called_with(None, None, None)

    @mock.patch("flumine.execution.simulatedexecution.time")
    def test_execute_update_paper_trade(self, mock_time):
        mock_order_package = mock.Mock(update_instructions=[], bet_delay=1)
        mock_order_package.__iter__ = mock.Mock(return_value=iter([]))
        mock_order_package.client.paper_trade = True
        self.execution.execute_update(mock_order_package, None)
        mock_time.sleep.assert_called_with(self.execution.UPDATE_LATENCY)

    @mock.patch("flumine.execution.simulatedexecution.SimulatedExecution._order_logger")
    def test_execute_replace(self, mock__order_logger):
        mock_order = mock.Mock()
        mock_order.trade.__enter__ = mock.Mock()
        mock_order.trade.__exit__ = mock.Mock()
        mock_order.market_id = "1.234"
        mock_order_package = mock.Mock(market_id="1.23")
        mock_order_package.client.paper_trade = False
        mock_order_package.__iter__ = mock.Mock(return_value=iter([mock_order]))
        mock_order_package.replace_instructions = [{"newPrice": 2.03}]
        mock_replacement_order = mock.Mock()
        mock_replacement_order_package = mock.Mock()
        mock_replacement_order_package.__iter__ = mock.Mock(
            return_value=iter([mock_order])
        )
        mock_sim_resp = mock.Mock()
        mock_sim_resp.status = "SUCCESS"
        mock_order.simulated.cancel.return_value = mock_sim_resp
        mock_replacement_order.simulated.place.return_value = mock_sim_resp
        mock_order.trade.create_order_replacement.return_value = mock_replacement_order
        self.execution.execute_replace(mock_order_package, None)
        mock_order.simulated.cancel.assert_called_with()
        mock_replacement_order.simulated.place.assert_called_with(
            mock_order_package.client,
            self.mock_market.market_book,
            {"newPrice": 2.03},
            self.execution._bet_id,
        )
        mock__order_logger.assert_has_calls(
            [
                call(mock_order, mock_sim_resp, OrderPackageType.CANCEL),
                call(
                    mock_replacement_order,
                    mock_sim_resp,
                    mock_order_package.package_type,
                ),
            ]
        )
        mock_order.execution_complete.assert_called_with()
        mock_replacement_order.executable.assert_called_with()
        mock_order.trade.__enter__.assert_called_with()
        mock_order.trade.__exit__.assert_called_with(None, None, None)

    @mock.patch("flumine.execution.simulatedexecution.SimulatedExecution._order_logger")
    def test_execute_replace_failure(self, mock__order_logger):
        mock_order = mock.Mock()
        mock_order.trade.__enter__ = mock.Mock()
        mock_order.trade.__exit__ = mock.Mock()
        mock_order_package = mock.Mock(market_id="1.23")
        mock_order_package.client.paper_trade = False
        mock_order_package.__iter__ = mock.Mock(return_value=iter([mock_order]))
        mock_order_package.replace_instructions = [{"newPrice": 2.54}]
        mock_replacement_order = mock.Mock()
        mock_replacement_order_package = mock.Mock()
        mock_replacement_order_package.__iter__ = mock.Mock(
            return_value=iter([mock_order])
        )
        mock_sim_resp = mock.Mock()
        mock_sim_resp.status = "FAILURE"
        mock_order.simulated.cancel.return_value = mock_sim_resp
        mock_replacement_order.simulated.place.return_value = mock_sim_resp
        mock_order.trade.create_order_replacement.return_value = mock_replacement_order
        self.execution.execute_replace(mock_order_package, None)
        mock_order.simulated.cancel.assert_called_with()
        mock_replacement_order.simulated.place.assert_called_with(
            mock_order_package.client,
            self.mock_market.market_book,
            {"newPrice": 2.54},
            self.execution._bet_id,
        )
        mock__order_logger.assert_called_with(
            mock_order, mock_sim_resp, OrderPackageType.CANCEL
        )
        mock_order.executable.assert_called_with()
        mock_replacement_order.executable.assert_not_called()
        mock_order.trade.__enter__.assert_called_with()
        mock_order.trade.__exit__.assert_called_with(None, None, None)

    @mock.patch("flumine.execution.simulatedexecution.time")
    def test_execute_replace_paper_trade(self, mock_time):
        mock_order_package = mock.Mock(
            market_id="1.23", replace_instructions=[], bet_delay=1
        )
        mock_order_package.__iter__ = mock.Mock(return_value=iter([]))
        mock_order_package.client.paper_trade = True
        self.execution.execute_replace(mock_order_package, None)
        mock_time.sleep.assert_called_with(self.execution.REPLACE_LATENCY + 1)
