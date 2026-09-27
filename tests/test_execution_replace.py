import unittest
from unittest import mock

from flumine.execution.baseexecution import OrderPackageType
from flumine.execution.betfairexecution import BetfairExecution


class BetfairExecutionReplaceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_flumine = mock.Mock()
        self.execution = BetfairExecution(self.mock_flumine)

    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._order_logger")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution.replace")
    @mock.patch("flumine.execution.betfairexecution.BetfairExecution._execution_helper")
    def test_execute_replace_matched_on_placement(
        self, mock__execution_helper, mock_replace, mock__order_logger
    ):
        """
        #743, a replace that is matched in full on placement (best price
        execution) returns orderStatus EXECUTION_COMPLETE, there is no size
        remaining so the replacement order must not be set executable.
        """
        mock_market = mock.Mock()
        self.mock_flumine.markets.markets = {"1.225432455": mock_market}
        mock_session = mock.Mock()
        mock_order = mock.Mock(market_id="1.225432455", bet_id="339845419341")
        mock_order.trade.__enter__ = mock.Mock()
        mock_order.trade.__exit__ = mock.Mock()
        mock_order_package = mock.MagicMock(market_id="1.225432455", info={})
        mock_order_package.__len__.return_value = 1
        mock_order_package.__iter__ = mock.Mock(return_value=iter([mock_order]))
        mock_report = mock.Mock()
        mock_instruction_report = mock.Mock()
        mock_instruction_report.cancel_instruction_reports.status = "SUCCESS"
        place_report = mock_instruction_report.place_instruction_reports
        place_report.status = "SUCCESS"
        place_report.bet_id = "339845613475"
        place_report.order_status = "EXECUTION_COMPLETE"
        place_report.size_matched = 0.01
        place_report.average_price_matched = 14.0
        mock_report.replace_instruction_reports = [mock_instruction_report]
        mock__execution_helper.return_value = mock_report
        self.execution.execute_replace(mock_order_package, mock_session)
        mock__execution_helper.assert_called_with(
            mock_replace, mock_order_package, mock_session
        )
        replacement_order = mock_order.trade.create_order_replacement()
        replacement_order.execution_complete.assert_called_with()
        replacement_order.executable.assert_not_called()
        mock_market.place_order.assert_called_with(
            replacement_order, execute=False, client=mock_order.client
        )
        mock__order_logger.assert_called_with(
            replacement_order,
            place_report,
            OrderPackageType.REPLACE,
        )
        mock_order.trade.__enter__.assert_called_with()
        mock_order.trade.__exit__.assert_called_with(None, None, None)
        mock_order_package.client.add_transaction.assert_called_with(1)
