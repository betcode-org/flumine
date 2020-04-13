import unittest
from unittest import mock

from flumine.order.order import BaseOrder, BetfairOrder, ExchangeType


class BaseOrderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_trade = mock.Mock()
        self.mock_status = mock.Mock()
        self.mock_order_type = mock.Mock()
        self.order = BaseOrder(
            self.mock_trade, "BACK", self.mock_order_type, 1, self.mock_status
        )

    def test_init(self):
        self.assertIsNotNone(self.order.id)
        self.assertEqual(self.order.trade, self.mock_trade)
        self.assertEqual(self.order.side, "BACK")
        self.assertEqual(self.order.order_type, self.mock_order_type)
        self.assertEqual(self.order.handicap, 1)
        self.assertEqual(self.order.status, self.mock_status)
        self.assertEqual(self.order.status_log, [self.mock_status])
        self.assertIsNone(self.order.bet_id)
        self.assertIsNone(self.order.EXCHANGE)

    def test_market_id(self):
        self.assertEqual(self.order.market_id, self.mock_trade.market_id)

    def test_selection_id(self):
        self.assertEqual(self.order.selection_id, self.mock_trade.selection_id)

    def test_lookup(self):
        self.assertEqual(
            self.order.lookup,
            (self.mock_trade.market_id, self.mock_trade.selection_id, 1),
        )

    def test_id_int(self):
        self.assertEqual(self.order.id_int, self.order.id.time)


class BetfairOrderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_trade = mock.Mock()
        self.mock_status = mock.Mock()
        self.mock_order_type = mock.Mock()
        self.order = BetfairOrder(
            self.mock_trade, "BACK", self.mock_order_type, self.mock_status
        )

    def test_init(self):
        self.assertEqual(self.order.EXCHANGE, ExchangeType.BETFAIR)
