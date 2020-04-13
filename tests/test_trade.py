import unittest
from unittest import mock

from flumine.order.trade import Trade


class TradeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.trade = Trade()

    # def test_init(self):
    #     self.assertEqual(self.trade._strategies, [])
