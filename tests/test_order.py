import unittest
from unittest import mock

from flumine.order.order import BaseOrder, BetfairOrder, ExchangeType


class BaseOrderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_status = mock.Mock()
        self.order = BaseOrder(self.mock_status)

    def test_init(self):
        self.assertEqual(self.order.status, self.mock_status)
        self.assertIsNone(self.order.EXCHANGE)


class BetfairOrderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.order = BetfairOrder()

    def test_init(self):
        self.assertEqual(self.order.EXCHANGE, ExchangeType.BETFAIR)
