"""Regression tests for order status derived from a place instruction report.

Covers #743: when Betfair returns orderStatus=EXECUTION_COMPLETE the order
crossed the book on placement. The report is authoritative, so the order must
not be published as EXECUTABLE.

These use a real BetfairOrder rather than a mock. The defect is in the state
the order ends up in, and a mock cannot hold state, so a mock-based test
cannot fail on it. Only the HTTP boundary is mocked.
"""

import unittest
from unittest import mock

from flumine.execution.betfairexecution import BetfairExecution
from flumine.order.order import BetfairOrder, OrderStatus
from flumine.order.ordertype import LimitOrder


class ExecutePlaceOrderStatusTest(unittest.TestCase):
    def setUp(self) -> None:
        self.execution = BetfairExecution(mock.Mock())

    def _order(self, size=10.0, price=2.0):
        trade = mock.Mock(market_id="1.234")
        trade.strategy.name_hash = "abcdefghijk"
        trade.__enter__ = mock.Mock()
        trade.__exit__ = mock.Mock(return_value=None)
        order = BetfairOrder(trade=trade, side="BACK", order_type=LimitOrder(size, price))
        order.bet_id = "123456789"
        order.place(publish_time=1, market_version=1, async_=False)
        return order

    def _execute(self, order, order_status):
        report = mock.Mock(
            status="SUCCESS",
            order_status=order_status,
            bet_id="123456789",
            instruction=mock.Mock(bet_id="123456789"),
        )
        response = mock.Mock(place_instruction_reports=[report])
        package = mock.MagicMock()
        package.__len__.return_value = 1
        package.__iter__ = mock.Mock(return_value=iter([order]))
        package.info = {}
        with mock.patch.object(self.execution, "_execution_helper", return_value=response):
            self.execution.execute_place(package, mock.Mock())

    def test_immediately_matched_is_execution_complete(self):
        """orderStatus=EXECUTION_COMPLETE must not leave the order EXECUTABLE."""
        order = self._order()
        self.assertEqual(order.status, OrderStatus.PENDING)

        self._execute(order, "EXECUTION_COMPLETE")

        self.assertEqual(
            order.status,
            OrderStatus.EXECUTION_COMPLETE,
            "venue reported EXECUTION_COMPLETE but order was left %s" % order.status,
        )
        self.assertTrue(order.complete)

    def test_resting_order_is_executable(self):
        """Control: a resting order must still go EXECUTABLE."""
        order = self._order()
        self._execute(order, "EXECUTABLE")
        self.assertEqual(order.status, OrderStatus.EXECUTABLE)
        self.assertFalse(order.complete)

    def test_expired_is_execution_complete(self):
        """Control: the pre-existing EXPIRED branch."""
        order = self._order()
        self._execute(order, "EXPIRED")
        self.assertEqual(order.status, OrderStatus.EXECUTION_COMPLETE)

    def test_pending_leaves_status_alone(self):
        """Control: an async PENDING report must not publish a status."""
        order = self._order()
        self._execute(order, "PENDING")
        self.assertEqual(order.status, OrderStatus.PENDING)


if __name__ == "__main__":
    unittest.main()