import unittest
from unittest import mock

from flumine.execution.baseexecution import OrderPackageType
from flumine.execution.betfairexecution import BetfairExecution


class BetfairExecutionPlaceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_flumine = mock.Mock()
        self.execution = BetfairExecution(self.mock_flumine)

    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._order_logger")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution.place")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._execution_helper")
    def test_execute_place_success_execution_complete(
        self, mock__execution_helper, mock_place, mock__order_logger
    ):
        """
        #743, a place that is matched in full on placement (best price
        execution) returns orderStatus EXECUTION_COMPLETE, there is no size
        remaining so the order must not be set executable.
        """
        mock_session = mock.Mock()
        mock_order = mock.Mock()
        mock_order.trade.__enter__ = mock.Mock()
        mock_order.trade.__exit__ = mock.Mock()
        mock_order_package = mock.MagicMock()
        mock_order_package.__len__.return_value = 1
        mock_order_package.__iter__ = mock.Mock(return_value=iter([mock_order]))
        mock_order_package.info = {}
        mock_report = mock.Mock()
        mock_instruction_report = mock.Mock(
            status="SUCCESS", order_status="EXECUTION_COMPLETE"
        )
        mock_report.place_instruction_reports = [mock_instruction_report]
        mock__execution_helper.return_value = mock_report
        self.execution.execute_place(mock_order_package, mock_session)
        mock__execution_helper.assert_called_with(
            mock_place, mock_order_package, mock_session
        )
        mock__order_logger.assert_called_with(
            mock_order, mock_instruction_report, OrderPackageType.PLACE
        )
        mock_order.execution_complete.assert_called_with()
        mock_order.executable.assert_not_called()
        mock_order.trade.__enter__.assert_called_with()
        mock_order.trade.__exit__.assert_called_with(None, None, None)
        mock_order_package.client.add_transaction.assert_called_with(1)

    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._order_logger")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution.place")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._execution_helper")
    def test_execute_place_success_pending(
        self, mock__execution_helper, mock_place, mock__order_logger
    ):
        mock_session = mock.Mock()
        mock_order = mock.Mock()
        mock_order.trade.__enter__ = mock.Mock()
        mock_order.trade.__exit__ = mock.Mock()
        mock_order_package = mock.MagicMock()
        mock_order_package.__len__.return_value = 1
        mock_order_package.__iter__ = mock.Mock(return_value=iter([mock_order]))
        mock_order_package.info = {}
        mock_report = mock.Mock()
        mock_instruction_report = mock.Mock(status="SUCCESS", order_status="PENDING")
        mock_report.place_instruction_reports = [mock_instruction_report]
        mock__execution_helper.return_value = mock_report
        self.execution.execute_place(mock_order_package, mock_session)
        mock__execution_helper.assert_called_with(
            mock_place, mock_order_package, mock_session
        )
        mock__order_logger.assert_called_with(
            mock_order, mock_instruction_report, OrderPackageType.PLACE
        )
        mock_order.executable.assert_not_called()
        mock_order.execution_complete.assert_not_called()
        mock_order.trade.__enter__.assert_called_with()
        mock_order.trade.__exit__.assert_called_with(None, None, None)
        mock_order_package.client.add_transaction.assert_called_with(1)

    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._order_logger")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution.place")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._execution_helper")
    def test_execute_place_success_expired(
        self, mock__execution_helper, mock_place, mock__order_logger
    ):
        mock_session = mock.Mock()
        mock_order = mock.Mock()
        mock_order.trade.__enter__ = mock.Mock()
        mock_order.trade.__exit__ = mock.Mock()
        mock_order_package = mock.MagicMock()
        mock_order_package.__len__.return_value = 1
        mock_order_package.__iter__ = mock.Mock(return_value=iter([mock_order]))
        mock_order_package.info = {}
        mock_report = mock.Mock()
        mock_instruction_report = mock.Mock(status="SUCCESS", order_status="EXPIRED")
        mock_report.place_instruction_reports = [mock_instruction_report]
        mock__execution_helper.return_value = mock_report
        self.execution.execute_place(mock_order_package, mock_session)
        mock__execution_helper.assert_called_with(
            mock_place, mock_order_package, mock_session
        )
        mock__order_logger.assert_called_with(
            mock_order, mock_instruction_report, OrderPackageType.PLACE
        )
        mock_order.executable.assert_not_called()
        mock_order.execution_complete.assert_called_with()
        mock_order.trade.__enter__.assert_called_with()
        mock_order.trade.__exit__.assert_called_with(None, None, None)
        mock_order_package.client.add_transaction.assert_called_with(1)

    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._order_logger")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution.place")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._execution_helper")
    def test_execute_place_success_executable(
        self, mock__execution_helper, mock_place, mock__order_logger
    ):
        mock_session = mock.Mock()
        mock_order = mock.Mock()
        mock_order.trade.__enter__ = mock.Mock()
        mock_order.trade.__exit__ = mock.Mock()
        mock_order_package = mock.MagicMock()
        mock_order_package.__len__.return_value = 1
        mock_order_package.__iter__ = mock.Mock(return_value=iter([mock_order]))
        mock_order_package.info = {}
        mock_report = mock.Mock()
        mock_instruction_report = mock.Mock(
            status="SUCCESS", order_status="EXECUTABLE"
        )
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
        mock_order.execution_complete.assert_not_called()
        mock_order.trade.__enter__.assert_called_with()
        mock_order.trade.__exit__.assert_called_with(None, None, None)
        mock_order_package.client.add_transaction.assert_called_with(1)

    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._order_logger")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution.place")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._execution_helper")
    def test_execute_place_success_order_status_none(
        self, mock__execution_helper, mock_place, mock__order_logger
    ):
        """
        A report carrying no order_status still falls through to
        executable(), which is what lets process.py pick the order up.
        """
        mock_session = mock.Mock()
        mock_order = mock.Mock()
        mock_order.trade.__enter__ = mock.Mock()
        mock_order.trade.__exit__ = mock.Mock()
        mock_order_package = mock.MagicMock()
        mock_order_package.__len__.return_value = 1
        mock_order_package.__iter__ = mock.Mock(return_value=iter([mock_order]))
        mock_order_package.info = {}
        mock_report = mock.Mock()
        mock_instruction_report = mock.Mock(status="SUCCESS", order_status=None)
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
        mock_order.execution_complete.assert_not_called()
        mock_order.trade.__enter__.assert_called_with()
        mock_order.trade.__exit__.assert_called_with(None, None, None)
        mock_order_package.client.add_transaction.assert_called_with(1)
