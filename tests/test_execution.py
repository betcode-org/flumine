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
        self.assertEqual(self.execution._bet_id, 100000000000)

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
        mock_order.responses.placed.assert_called_with(mock_instruction_report)

    def test_handler_queue(self):
        self.assertEqual(self.execution.handler_queue, self.mock_flumine.handler_queue)

    def test_markets(self):
        self.assertEqual(self.execution.markets, self.mock_flumine.markets)

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

    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._order_logger")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution.place")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._execution_helper")
    def test_execute_place_failure(
        self, mock__execution_helper, mock_place, mock__order_logger
    ):
        mock_session = mock.Mock()
        mock_order = mock.Mock()
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

    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._order_logger")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution.place")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._execution_helper")
    def test_execute_place_timeout(
        self, mock__execution_helper, mock_place, mock__order_logger
    ):
        mock_session = mock.Mock()
        mock_order = mock.Mock()
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

    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._order_logger")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution.cancel")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._execution_helper")
    def test_execute_cancel_success_partial(
        self, mock__execution_helper, mock_cancel, mock__order_logger
    ):
        mock_session = mock.Mock()
        mock_order = mock.Mock()
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

    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._order_logger")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution.cancel")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._execution_helper")
    def test_execute_cancel_failure(
        self, mock__execution_helper, mock_cancel, mock__order_logger
    ):
        mock_session = mock.Mock()
        mock_order = mock.Mock()
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

    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._order_logger")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution.cancel")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._execution_helper")
    def test_execute_cancel_timeout(
        self, mock__execution_helper, mock_cancel, mock__order_logger
    ):
        mock_session = mock.Mock()
        mock_order = mock.Mock()
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

    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._order_logger")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution.cancel")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._execution_helper")
    def test_execute_cancel_not_returned(
        self, mock__execution_helper, mock_cancel, mock__order_logger
    ):
        mock_session = mock.Mock()
        mock_order = mock.Mock()
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

    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._order_logger")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution.update")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._execution_helper")
    def test_execute_update_failure(
        self, mock__execution_helper, mock_update, mock__order_logger
    ):
        mock_session = mock.Mock()
        mock_order = mock.Mock()
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

    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._order_logger")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution.update")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._execution_helper")
    def test_execute_update_timeout(
        self, mock__execution_helper, mock_update, mock__order_logger
    ):
        mock_session = mock.Mock()
        mock_order = mock.Mock()
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
        mock_session = mock.Mock()
        mock_order = mock.Mock()
        mock_order.market_id = "1.234"
        mock_order.bet_id = 123
        mock_order_package = mock.Mock()
        mock_order_package.__iter__ = mock.Mock(return_value=iter([mock_order]))
        mock_order_package.info = {}
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
        mock_order_package.market.place_order.assert_called_with(
            replacement_order, execute=False
        )
        mock__order_logger.assert_called_with(
            replacement_order,
            mock_instruction_report.place_instruction_reports,
            OrderPackageType.REPLACE,
        )

    # def test_execute_replace_failure(self):
    #     pass

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

    def test__execution_helper(self):
        mock_trading_function = mock.Mock()
        mock_trading_function.__name__ = "test"
        mock_session = mock.Mock()
        mock_order_package = mock.Mock()
        mock_order_package.info = {}
        self.execution._execution_helper(
            mock_trading_function, mock_order_package, mock_session
        )
        mock_trading_function.assert_called_with(mock_order_package, mock_session)


class SimulatedExecutionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_flumine = mock.Mock()
        self.execution = SimulatedExecution(self.mock_flumine)

    def test_init(self):
        self.assertEqual(self.execution.EXCHANGE, ExchangeType.SIMULATED)

    @mock.patch("flumine.execution.simulatedexecution.SimulatedExecution.execute_place")
    def test_handler_place(self, mock_execute_place):
        mock_order_package = mock.Mock()
        mock_order_package.package_type = OrderPackageType.PLACE
        self.execution.handler(mock_order_package)
        mock_execute_place.assert_called_with(mock_order_package, http_session=None)

    @mock.patch(
        "flumine.execution.simulatedexecution.SimulatedExecution.execute_cancel"
    )
    def test_handler_cancel(self, mock_execute_cancel):
        mock_order_package = mock.Mock()
        mock_order_package.package_type = OrderPackageType.PLACE.CANCEL
        self.execution.handler(mock_order_package)
        mock_execute_cancel.assert_called_with(mock_order_package, http_session=None)

    @mock.patch(
        "flumine.execution.simulatedexecution.SimulatedExecution.execute_update"
    )
    def test_handler_update(self, mock_execute_update):
        mock_order_package = mock.Mock()
        mock_order_package.package_type = OrderPackageType.UPDATE
        self.execution.handler(mock_order_package)
        mock_execute_update.assert_called_with(mock_order_package, http_session=None)

    @mock.patch(
        "flumine.execution.simulatedexecution.SimulatedExecution.execute_replace"
    )
    def test_handler_replace(self, mock_execute_replace):
        mock_order_package = mock.Mock()
        mock_order_package.package_type = OrderPackageType.REPLACE
        self.execution.handler(mock_order_package)
        mock_execute_replace.assert_called_with(mock_order_package, http_session=None)

    @mock.patch("flumine.execution.simulatedexecution.SimulatedExecution._order_logger")
    def test_execute_place_success(self, mock__order_logger):
        mock_order = mock.Mock()
        mock_order_package = mock.Mock()
        mock_order_package.__iter__ = mock.Mock(return_value=iter([mock_order]))
        mock_order_package.place_instructions = [1]
        mock_order_package.info = {}
        mock_sim_resp = mock.Mock()
        mock_sim_resp.status = "SUCCESS"
        mock_order.simulated.place.return_value = mock_sim_resp
        self.execution.execute_place(mock_order_package, None)
        mock_order.simulated.place.assert_called_with(
            mock_order_package.market.market_book, 1, self.execution._bet_id
        )
        mock__order_logger.assert_called_with(
            mock_order, mock_sim_resp, mock_order_package.package_type
        )
        mock_order.executable.assert_called_with()

    @mock.patch("flumine.execution.simulatedexecution.SimulatedExecution._order_logger")
    def test_execute_place_failure(self, mock__order_logger):
        mock_order = mock.Mock()
        mock_order_package = mock.Mock()
        mock_order_package.__iter__ = mock.Mock(return_value=iter([mock_order]))
        mock_order_package.place_instructions = [1]
        mock_order_package.info = {}
        mock_sim_resp = mock.Mock()
        mock_sim_resp.status = "FAILURE"
        mock_order.simulated.place.return_value = mock_sim_resp
        self.execution.execute_place(mock_order_package, None)
        mock_order.simulated.place.assert_called_with(
            mock_order_package.market.market_book, 1, self.execution._bet_id
        )
        mock__order_logger.assert_called_with(
            mock_order, mock_sim_resp, mock_order_package.package_type
        )
        mock_order.lapsed.assert_called_with()

    @mock.patch("flumine.execution.simulatedexecution.SimulatedExecution._order_logger")
    def test_execute_cancel(self, mock__order_logger):
        mock_order = mock.Mock()
        mock_order_package = mock.Mock()
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

    @mock.patch("flumine.execution.simulatedexecution.SimulatedExecution._order_logger")
    def test_execute_cancel_failure(self, mock__order_logger):
        mock_order = mock.Mock()
        mock_order_package = mock.Mock()
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

    def test_execute_update(self):
        with self.assertRaises(NotImplementedError):
            self.execution.execute_update(None, None)

    def test_execute_replace(self):
        with self.assertRaises(NotImplementedError):
            self.execution.execute_replace(None, None)
