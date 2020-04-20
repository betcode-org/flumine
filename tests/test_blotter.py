import unittest
from unittest import mock

from flumine.markets.blotter import Blotter, OrderStatus


class BlotterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.blotter = Blotter("1.234")

    def test_init(self):
        self.assertEqual(self.blotter.market_id, "1.234")
        self.assertEqual(self.blotter._orders, {})

    def test_strategy_orders(self):
        mock_order = mock.Mock()
        mock_order.trade.strategy = 69
        self.blotter._orders = {"12345": mock_order}
        self.assertEqual(self.blotter.strategy_orders(12), [])
        self.assertEqual(self.blotter.strategy_orders(69), [mock_order])

    def test_live_orders(self):
        self.assertFalse(self.blotter.live_orders)
        mock_order = mock.Mock()
        mock_order.status = OrderStatus.EXECUTABLE
        self.blotter._orders = {"12345": mock_order}
        self.assertTrue(self.blotter.live_orders)

    def test__contains(self):
        self.blotter._orders = {"123": "test"}
        self.assertIn("123", self.blotter)
        self.assertNotIn("321", self.blotter)

    def test__setitem(self):
        self.blotter["123"] = "test"
        self.assertEqual(self.blotter._orders, {"123": "test"})

    def test__getitem(self):
        self.blotter._orders = {"12345": "test", "54321": "test2"}
        self.assertEqual(self.blotter["12345"], "test")
        self.assertEqual(self.blotter["54321"], "test2")

    def test__len(self):
        self.blotter._orders = {"12345": "test", "54321": "test"}
        self.assertEqual(len(self.blotter), 2)
