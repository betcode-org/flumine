import unittest
from unittest import mock

from flumine.order.trade import Trade


class TradeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_strategy = mock.Mock()
        self.mock_fill_kill = mock.Mock()
        self.mock_green = mock.Mock()
        self.mock_stop = mock.Mock()
        self.trade = Trade(
            "1.234",
            567,
            self.mock_strategy,
            self.mock_fill_kill,
            self.mock_green,
            self.mock_stop,
        )

    def test_init(self):
        self.assertEqual(self.trade.market_id, "1.234")
        self.assertEqual(self.trade.selection_id, 567)
        self.assertEqual(self.trade.strategy, self.mock_strategy)
        self.assertEqual(self.trade.fill_kill, self.mock_fill_kill)
        self.assertEqual(self.trade.green, self.mock_green)
        self.assertEqual(self.trade.stop, self.mock_stop)
        self.assertEqual(self.trade.orders, [])
